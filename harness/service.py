from __future__ import annotations

import threading

from harness.config import ROOT, Settings, load_target
from harness.controller import Controller
from harness.errors import HarnessError
from harness.models import OllamaModelClient, ScriptedModelClient, tool_reply
from harness.sandbox import DockerRunner
from harness.store import RunStore
from harness.workspace import RunLock, Workspace


def scripted_demo() -> ScriptedModelClient:
    """Disclosed simulation; real Ollama runs never use these prepared responses."""
    return ScriptedModelClient([
        tool_reply("read_file", path="shopping_cart.py", start_line=39, end_line=50),
        tool_reply("replace_text", path="shopping_cart.py",
                   old="offer.argument * (quantity_as_int / x)",
                   new="offer.argument * (quantity_as_int // x)"),
        tool_reply("run_check", check_id="acceptance"),
        tool_reply("finish", summary="Simulierter Paketpreis-Fix; Endprüfung anfordern."),
    ])


class RunService:
    """One process-wide worker, shared across Streamlit sessions and reruns."""
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

    def start(self, task: str, provider: str, *, baseline_only=False) -> str:
        if not task.strip() or len(task) > 12000:
            raise HarnessError("Aufgabe muss 1 bis 12000 Zeichen enthalten")
        if provider not in {"ollama", "scripted"}:
            raise HarnessError("Unbekannter Provider")
        target = load_target()
        with self.mutex:
            if self.active:
                raise HarnessError("Ein Lauf ist bereits aktiv")
            lock = RunLock(self.home)
            pending = list((self.home / "runs").glob("*/active-container.json"))
            if pending:
                lock.close()
                raise HarnessError("Containerende eines früheren Laufs ist unbestätigt. "
                                   "Zuerst dessen active-container.json prüfen und eigenen Container entfernen: "
                                   + str(pending[0]))
            self.cancel_event = threading.Event()
            self.report, self.error, self.controller = None, None, None
            self.workspace = Workspace(target, self.home)
            self.store = RunStore(self.workspace.path, self.settings.limits.artifact_bytes)

            def work():
                try:
                    self.store.event("state", state="preparing")
                    self.workspace.create()
                    runner = DockerRunner(self.workspace.repo, ROOT / "checks", self.settings.image,
                                          self.workspace.run_id, self.settings.limits)
                    model = OllamaModelClient(self.settings) if provider == "ollama" else scripted_demo()
                    self.controller = Controller(self.workspace, self.settings, model, runner,
                                                 self.store, self.cancel_event, task)
                    self.report = self.controller.run(baseline_only=baseline_only)
                except Exception as exc:
                    self.error = f"{type(exc).__name__}: {exc}"
                    self.store.event("error", message=self.error)
                    self.report = self.store.report({"run_id": self.workspace.run_id, "state": "blocked",
                        "success": False, "reason": self.error, "checks": [],
                        "provider": provider, "simulated": provider == "scripted"})
                finally:
                    lock.close()

            self.thread = threading.Thread(target=work, name="harness-controller", daemon=False)
            self.thread.start()
            return self.workspace.run_id

    def cancel(self) -> None:
        self.cancel_event.set()

    def snapshot(self) -> dict:
        # Mutable event data is copied under RunStore's lock. Reports are assigned once.
        return {"active": self.active, "events": self.store.snapshot() if self.store else [],
                "report": self.report, "error": self.error,
                "run_id": self.workspace.run_id if self.workspace else None,
                "path": str(self.workspace.path) if self.workspace else None,
                "actions": self.controller.actions if self.controller else 0,
                "state": self.controller.state if self.controller else "ready"}
