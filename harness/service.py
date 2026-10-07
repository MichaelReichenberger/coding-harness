"""Startet genau einen Controller im Hintergrund und liefert UI-Snapshots."""

from __future__ import annotations

import threading

from harness.config import ROOT, Settings, load_target
from harness.controller import Controller
from harness.errors import HarnessError
from harness.models import OllamaModelClient
from harness.sandbox import DockerRunner
from harness.store import RunStore
from harness.workspace import RunLock, Workspace


class RunService:
    """Trennt den langsamen Lauf von der Oberfläche, damit Abbrechen bedienbar bleibt.

    Der Thread-Lock schützt Startanfragen innerhalb dieses Prozesses. RunLock
    schützt zusätzlich vor einem parallelen Start durch einen CLI-Prozess.
    """

    def __init__(self, settings: Settings, home=None):
        self.settings = settings
        self.home = home or ROOT / ".harness"
        self.thread: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.store = None
        self.report = None
        self.error = None
        self.workspace = None
        self.controller = None
        self.mutex = threading.Lock()

    @property
    def active(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, task: str, *, baseline_only=False, model_name: str | None = None) -> str:
        if not task.strip() or len(task) > 12000:
            raise HarnessError("Aufgabe muss 1 bis 12000 Zeichen enthalten")
        # Der UI-Modellname wird genauso validiert wie die Konfigurationsdatei.
        # Die Kopie gilt nur für diesen Lauf; spätere UI-Eingaben ändern ihn nicht.
        settings_data = self.settings.model_dump()
        if model_name is not None:
            settings_data["model"] = model_name
        settings = Settings.model_validate(settings_data)
        target = load_target()
        with self.mutex:
            if self.active:
                raise HarnessError("Ein Lauf ist bereits aktiv")
            lock = RunLock(self.home)
            pending = list((self.home / "runs").glob("*/active-container.json"))
            if pending:
                lock.close()
                raise HarnessError(
                    "Containerende eines früheren Laufs ist unbestätigt. "
                    "Zuerst dessen active-container.json prüfen und eigenen Container entfernen: "
                    + str(pending[0])
                )
            self.cancel_event = threading.Event()
            self.report, self.error, self.controller = None, None, None
            self.workspace = Workspace(target, self.home)
            self.store = RunStore(self.workspace.path, self.settings.limits.artifact_bytes)

            def work():
                try:
                    self.store.event("state", state="preparing")
                    self.workspace.create()
                    runner = DockerRunner(
                        self.workspace.repo,
                        ROOT / "checks",
                        self.settings.image,
                        self.workspace.run_id,
                        self.settings.limits,
                    )
                    model = OllamaModelClient(settings)
                    self.controller = Controller(
                        self.workspace, settings, model, runner, self.store, self.cancel_event, task
                    )
                    self.report = self.controller.run(baseline_only=baseline_only)
                except Exception as exc:
                    self.error = f"{type(exc).__name__}: {exc}"
                    self.store.event("error", message=self.error)
                    self.report = self.store.report(
                        {
                            "run_id": self.workspace.run_id,
                            "state": "blocked",
                            "success": False,
                            "reason": self.error,
                            "checks": [],
                            "provider": "ollama",
                            "simulated": False,
                            "task": task,
                            "model": settings.model,
                        }
                    )
                finally:
                    lock.close()

            self.thread = threading.Thread(target=work, name="harness-controller", daemon=False)
            self.thread.start()
            return self.workspace.run_id

    def cancel(self) -> None:
        self.cancel_event.set()

    def snapshot(self) -> dict:
        # Mutable event data is copied under RunStore's lock. Reports are assigned once.
        return {
            "active": self.active,
            "events": self.store.snapshot() if self.store else [],
            "report": self.report,
            "error": self.error,
            "run_id": self.workspace.run_id if self.workspace else None,
            "path": str(self.workspace.path) if self.workspace else None,
            "actions": self.controller.actions if self.controller else 0,
            "state": self.controller.state if self.controller else "ready",
        }
