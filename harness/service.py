"""UI-/CLI-unabhängiger Sitzungsdienst mit Worker und prozessübergreifender Sperre.

S2-I/S: Start, Öffnen, Abbruch und Resume laufen hier zusammen. Nur der Worker
besitzt einen Controller. Die Oberfläche führt weder Zielcode noch Werkzeuge aus.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

from harness.config import FEATURE_CRITERIA, PROFILES, ROOT, Settings, Target, select_project
from harness.controller import Controller
from harness.errors import HarnessError
from harness.models import OllamaModelClient
from harness.repository import tool_schemas
from harness.sandbox import CHECKS, FEATURE_CHECKS, DockerRunner
from harness.sessions import SessionStore
from harness.store import RunStore
from harness.workspace import RunLock, Workspace, tree_hashes


class RunService:
    def __init__(self, settings: Settings, home=None):
        self.settings = settings
        self.home = Path(home or ROOT / ".harness")
        self.thread = None
        self.cancel_event = threading.Event()
        self.store = self.report = self.workspace = self.controller = None
        self.error = None
        self.mutex = threading.Lock()
        self.saved_state = "ready"
        self.diff = None

    @property
    def active(self):
        return self.thread is not None and self.thread.is_alive()

    def policy(self, target, settings, project, profile):
        """Aktuelle vertrauenswürdige Rechte, Kriterien und Prüffiles vergleichen."""
        return {
            "target": target.model_dump(),
            "settings": settings.model_dump(),
            "project": project,
            "profile": profile,
            "criteria": FEATURE_CRITERIA if profile == "feature" else "Stage-1 receipt display",
            "checks": FEATURE_CHECKS if profile == "feature" else CHECKS,
            "trusted_hashes": tree_hashes(ROOT / "checks"),
            "tools_sha256": hashlib.sha256(
                json.dumps(tool_schemas(), sort_keys=True).encode()
            ).hexdigest(),
        }

    def start(
        self, task, *, baseline_only=False, model_name=None, project="supermarket", profile="bugfix"
    ):
        if not task.strip() or len(task) > 12000:
            raise HarnessError("Aufgabe muss 1 bis 12000 Zeichen enthalten")
        if profile not in PROFILES:
            raise HarnessError("Unbekannte Aufgabenart")
        target = select_project(project)
        data = self.settings.model_dump()
        if model_name is not None:
            data["model"] = model_name
        settings = Settings.model_validate(data)
        workspace = Workspace(target, self.home)
        return self._launch(
            workspace, settings, project, profile, task, baseline_only=baseline_only
        )

    def _launch(
        self, workspace, settings, project, profile, task, *, baseline_only=False, resume=False
    ):
        with self.mutex:
            if self.active:
                raise HarnessError("Ein Lauf ist bereits aktiv")
            lock = RunLock(self.home)
            try:
                session = SessionStore(self.home, workspace.run_id, settings.limits.artifact_bytes)
                pending = list((self.home / "runs").glob("*/active-container.json"))
                if pending:
                    if resume:
                        session.pause("Containerende unbestätigt")
                    raise HarnessError(
                        "Containerende unbestätigt; eigenen Container zuerst prüfen: "
                        + str(pending[0])
                    )
                policy = self.policy(workspace.target, settings, project, profile)
                checkpoint = session.validate(workspace, policy) if resume else None
                if resume:
                    (session.path / "cancel.request").unlink(missing_ok=True)
                    (session.path / "pause.json").unlink(missing_ok=True)
                self.workspace = workspace
                self.store = RunStore(workspace.path, settings.limits.artifact_bytes)
                self.cancel_event = threading.Event()
                self.report = self.error = self.controller = None
                self.saved_state = "preparing"
                self.diff = None
            except Exception:
                lock.close()
                raise

            def work():
                done = threading.Event()

                def watch_cancel():
                    # Externes `cancel ID` wirkt auch während einer HTTP-Anfrage.
                    while not done.wait(0.05):
                        if (session.path / "cancel.request").exists():
                            self.cancel_event.set()
                            return

                watcher = threading.Thread(target=watch_cancel, daemon=True)
                watcher.start()
                try:
                    if not resume:
                        # Aufgabe schon vor Export/Modell speichern. Bei hartem Absturz
                        # in der Vorbereitung bleibt pending=prepare sichtbar.
                        session.write(
                            {
                                "task": task,
                                "project": project,
                                "profile": profile,
                                "policy": policy,
                                "state": "preparing",
                                "pending": {"kind": "prepare"},
                            }
                        )
                        self.store.event("state", state="preparing")
                        workspace.create()
                    runner = DockerRunner(
                        workspace.repo,
                        ROOT / "checks",
                        settings.image,
                        workspace.run_id,
                        settings.limits,
                    )
                    runner.checks = {k: list(v) for k, v in policy["checks"].items()}
                    self.controller = Controller(
                        workspace,
                        settings,
                        OllamaModelClient(settings),
                        runner,
                        self.store,
                        self.cancel_event,
                        task,
                        profile=profile,
                        project=project,
                        session=session,
                        policy=policy,
                        checkpoint=checkpoint,
                    )
                    self.report = self.controller.run(baseline_only=baseline_only)
                except Exception as exc:
                    self.error = f"{type(exc).__name__}: {exc}"
                    self.store.event("error", message=self.error)
                    self.report = self.store.report(
                        {
                            "run_id": workspace.run_id,
                            "state": "blocked",
                            "success": False,
                            "reason": self.error,
                            "checks": [],
                            "task": task,
                            "project": project,
                            "profile": profile,
                            "model": settings.model,
                            "simulated": False,
                        }
                    )
                finally:
                    done.set()
                    watcher.join(timeout=1)
                    lock.close()

            self.thread = threading.Thread(target=work, name="harness-controller", daemon=False)
            self.thread.start()
            return workspace.run_id

    def resume(self, run_id):
        session = SessionStore(self.home, run_id, self.settings.limits.artifact_bytes)
        data = session.load()
        target = select_project(data["project"])
        if data["profile"] not in PROFILES:
            raise HarnessError("Sitzung pausiert: Aufgabenart nicht mehr erlaubt")
        # Das gewählte Modell gehört zur Sitzung; neue Limits/Serveradressen dürfen
        # dagegen nicht unbemerkt die ursprünglich gültige Policy ersetzen.
        settings = Settings.model_validate(
            dict(self.settings.model_dump(), model=data["policy"]["settings"]["model"])
        )
        workspace = Workspace.reopen(target, self.home, run_id)
        return self._launch(
            workspace, settings, data["project"], data["profile"], data["task"], resume=True
        )

    def cancel(self, run_id=None):
        if run_id is None or (self.workspace and run_id == self.workspace.run_id):
            self.cancel_event.set()
        if run_id is not None:
            SessionStore(self.home, run_id, self.settings.limits.artifact_bytes).cancel()

    def sessions(self):
        items = []
        for path in sorted((self.home / "runs").glob("*/session.json"), reverse=True)[:100]:
            try:
                session = SessionStore(
                    self.home, path.parent.name, self.settings.limits.artifact_bytes
                )
                data = session.load()
                paused = data.get("pending") or (session.path / "pause.json").exists()
                items.append(
                    {
                        "run_id": path.parent.name,
                        "state": "paused" if paused else data["state"],
                        "project": data["project"],
                        "profile": data["profile"],
                        "task": data["task"][:100],
                    }
                )
            except Exception as exc:
                items.append({"run_id": path.parent.name, "state": "unreadable", "error": str(exc)})
        return items

    def open(self, run_id):
        """Nur Metadaten/Diff öffnen, nie Zielcode ausführen oder Quellen zurücksetzen."""
        with self.mutex:
            if self.active:
                raise HarnessError("Aktiver Lauf muss zuerst beendet werden")
            session = SessionStore(self.home, run_id, self.settings.limits.artifact_bytes)
            data = session.load()
            self.workspace = Workspace.reopen(
                Target.model_validate(data["policy"]["target"]), self.home, run_id
            )
            self.store = RunStore(session.path, self.settings.limits.artifact_bytes)
            path = session.path / "report.json"
            self.report = (
                json.loads(path.read_text("utf-8"))
                if path.exists()
                else {
                    "state": "paused",
                    "reason": "Unterbrochene Sitzung",
                    "success": False,
                    "task": data["task"],
                    "checks": data.get("checks", []),
                    "steps": data.get("steps", []),
                }
            )
            self.controller = None
            pause_path = session.path / "pause.json"
            if data.get("pending") or pause_path.exists():
                reason = (
                    json.loads(pause_path.read_text("utf-8"))["reason"]
                    if pause_path.exists()
                    else "Unsichere unterbrochene Aktion"
                )
                self.report = dict(
                    self.report,
                    state="paused",
                    success=False,
                    reason=reason,
                    pending=data.get("pending"),
                )
            try:
                diff, changed, truncated = self.workspace.diff(
                    self.settings.limits.artifact_bytes // 4
                )
                self.report.update(changed_files=changed, diff_truncated=truncated)
                self.diff = diff
            except (OSError, ValueError, HarnessError) as exc:
                self.report = dict(self.report, state="paused", success=False, reason=str(exc))
                self.diff = ""
            self.saved_state = self.report["state"]
            return {
                "session": data,
                "report": self.report,
                "diff": self.diff,
            }

    def snapshot(self):
        active = self.active
        report = self.report
        controller = self.controller
        state = self.saved_state
        actions = 0
        if controller:
            state = controller.state
            actions = controller.actions
        elif report:
            actions = report.get("actions", 0)
        if report and not active:
            state = report["state"]
        return {
            "active": active,
            "events": self.store.snapshot() if self.store else [],
            "report": report,
            "diff": self.diff,
            "error": self.error,
            "run_id": self.workspace.run_id if self.workspace else None,
            "path": str(self.workspace.path) if self.workspace else None,
            "actions": actions,
            "state": state,
        }
