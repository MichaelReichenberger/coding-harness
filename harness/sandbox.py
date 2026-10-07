"""Einweg-Linux-Container für Zielcode; niemals Ausführung auf dem Host.

CHECKS ordnet erlaubte Namen festen Argumentlisten zu. Das Modell kann weder
Containeroptionen ändern noch eigene Host-Befehle einschleusen. Jeder Check
erhält einen neuen Container und endet erst nach geprüftem Cleanup.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from harness.config import Limits
from harness.errors import SandboxError
from harness.process import capture
from harness.workspace import tree_hashes

CheckStatus = Literal["passed", "failed", "unavailable", "not_run"]
CHECKS = {
    "acceptance": ["python", "-I", "/trusted/entry.py", "acceptance"],
    "regression_core": ["python", "-I", "/trusted/entry.py", "regression_core"],
    "regression_pricing": ["python", "-I", "/trusted/entry.py", "regression_pricing"],
}


@dataclass
class CheckResult:
    """Strukturiertes Ergebnis: Textkürzung verliert weder Exit-Code noch Status."""

    check_id: str
    status: CheckStatus = "not_run"
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    timed_out: bool = False
    cancelled: bool = False
    seconds: float = 0
    reason: str = ""
    container: str = ""
    cleanup_verified: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class DockerRunner:
    """Baut die Isolationsgrenze und beendet auch Kindprozesse des Zielcodes.

    poisoned bedeutet: Das Ende des letzten Containers konnte nicht bestätigt
    werden. In diesem Zustand sind weitere Aktionen verboten, auch wenn ein
    einzelner CLI-Aufruf scheinbar erfolgreich war.
    """

    def __init__(
        self,
        repo: Path,
        trusted: Path,
        image: str,
        run_id: str,
        limits: Limits,
        gate: threading.RLock | None = None,
    ):
        self.checks = {key: list(command) for key, command in CHECKS.items()}
        self.repo, self.trusted = repo.resolve(), trusted.resolve()
        self.image, self.run_id, self.limits = image, run_id, limits
        self.gate = gate or threading.RLock()
        self.hashes = tree_hashes(self.trusted)
        self.poisoned = False

    def inspect_environment(self) -> dict:
        info = capture(["docker", "info", "--format", "{{.OSType}}"], timeout=10)
        if info.exit_code or info.timed_out:
            raise SandboxError(info.stderr or "Docker-Daemon antwortet nicht")
        if info.stdout.strip() != "linux":
            raise SandboxError(
                "Docker meldet keine nutzbare Linux-Engine: "
                + (info.stderr or info.stdout or "leere Antwort").strip()
            )
        result = capture(
            ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"], timeout=10
        )
        if result.exit_code or result.timed_out:
            raise SandboxError("Sandbox-Image fehlt: python -m harness setup --build")
        # Image-ID für den ganzen Lauf fixieren: ein später neu gesetzter Tag
        # darf Baseline und Endprüfung nicht mit unterschiedlichen Images starten.
        self.image = result.stdout.strip()
        return {"platform": "linux", "image_id": self.image}

    def create_command(self, name: str, command: list[str]) -> list[str]:
        # Zwei lesbare Mounts, kein Netzwerk, keine Host-Secrets, keine Root-UID.
        # Quelländerungen erfolgen nur über RepositoryTools auf dem Host.
        for path in [self.repo, self.trusted]:
            if "," in str(path):
                raise SandboxError("Docker-Mountpfade dürfen kein Komma enthalten")
        args = [
            "docker",
            "create",
            "--name",
            name,
            "--label",
            f"harness.run={self.run_id}",
            "--network",
            "none",
            "--read-only",
            "--user",
            "10001:10001",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            "512m",
            "--memory-swap",
            "512m",
            "--cpus",
            "1",
            "--init",
            "--log-driver",
            "none",
            "--workdir",
            "/repo",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--env",
            "PYTHONUNBUFFERED=1",
            "--env",
            "PYTHONIOENCODING=utf-8",
            "--env",
            "HOME=/tmp",
            "--mount",
            f"type=bind,source={self.repo},target=/repo,readonly",
            "--mount",
            f"type=bind,source={self.trusted},target=/trusted,readonly",
        ]
        args += ["--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=700"]
        return args + [self.image, *command]

    def _cleanup(self, name: str) -> bool:
        # Nur unseren vorher erzeugten, zufälligen Namen entfernen. Ein beendeter
        # docker-CLI-Prozess beweist NICHT, dass der Container beendet ist.
        capture(["docker", "stop", "--time", "1", name], timeout=6)
        for _ in range(2):
            capture(["docker", "rm", "--force", name], timeout=10)
            remaining = capture(
                ["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.Names}}"],
                timeout=10,
            )
            if (
                remaining.exit_code == 0
                and not remaining.timed_out
                and not remaining.stdout.strip()
            ):
                return True
        self.poisoned = True
        return False

    def run(self, check_id: str, cancel: threading.Event) -> CheckResult:
        if check_id not in self.checks:
            raise SandboxError("Unbekannte Check-ID")
        with self.gate:
            if self.poisoned:
                raise SandboxError("Containerende unbestätigt; weitere Aktionen gesperrt")
            if tree_hashes(self.trusted) != self.hashes:
                raise SandboxError("Integrität der geschützten Prüffiles verletzt")
            if cancel.is_set():
                return CheckResult(check_id, cancelled=True, reason="Abgebrochen")
            result = self.execute(self.checks[check_id], cancel, check_id)
            if tree_hashes(self.trusted) != self.hashes:
                raise SandboxError("Prüffiles wurden während des Checks verändert")
            return result

    def execute(
        self, command: list[str], cancel: threading.Event, check_id="boundary"
    ) -> CheckResult:
        """Interner Aufruf für Checks/Grenztests, kein Werkzeug für das Modell."""
        name = f"harness-{self.run_id}-{uuid.uuid4().hex[:8]}".lower()
        result = CheckResult(check_id, command=list(command), container=name)
        started = time.monotonic()
        registry = self.repo.parent / "active-container.json"
        # Vor docker create speichern: Auch bei einem Harness-Absturz ist der
        # möglicherweise weiterlaufende Container eindeutig zuordenbar.
        registry.write_text(json.dumps({"name": name, "run_id": self.run_id}), "utf-8")
        try:
            creation = capture(
                self.create_command(name, command),
                timeout=20,
                limit=self.limits.output_bytes,
                cancel=cancel,
            )
            if creation.exit_code or creation.timed_out or creation.cancelled:
                result.status = "unavailable"
                result.reason = "Container konnte nicht erstellt werden"
                result.stderr = creation.stderr
                result.cancelled = creation.cancelled
                result.timed_out = creation.timed_out
                return result
            execution = capture(
                ["docker", "start", "--attach", name],
                timeout=self.limits.check_seconds,
                limit=self.limits.output_bytes,
                cancel=cancel,
            )
            result.stdout, result.stderr = execution.stdout, execution.stderr
            result.truncated, result.timed_out = execution.truncated, execution.timed_out
            result.cancelled = execution.cancelled or cancel.is_set()
            state = capture(["docker", "inspect", "--format", "{{json .State}}", name], timeout=10)
            if state.exit_code == 0 and not state.timed_out:
                info = json.loads(state.stdout)
                result.exit_code = info["ExitCode"] if not info["Running"] else None
                result.status = "passed" if result.exit_code == 0 else "failed"
                if info.get("Error"):
                    result.status, result.reason = "unavailable", info["Error"]
                if info.get("OOMKilled"):
                    result.reason = "Container-Speicherlimit erreicht"
            else:
                result.status = "unavailable"
                result.reason = "Containerstatus nicht lesbar"
            if result.timed_out or result.cancelled:
                result.status = "failed"
                result.reason = "Abgebrochen" if result.cancelled else "Zeitlimit erreicht"
        except (OSError, ValueError) as exc:
            result.status, result.reason = "unavailable", str(exc)
        finally:
            # Gilt bei Erfolg, Fehler, Timeout UND Abbruch. Ohne bestätigtes Ende
            # bleibt die Registry-Datei liegen und RunService sperrt neue Läufe.
            try:
                result.cleanup_verified = self._cleanup(name)
            except OSError:
                self.poisoned = True
            result.seconds = round(time.monotonic() - started, 3)
            if result.cleanup_verified:
                registry.unlink(missing_ok=True)
            else:
                self.poisoned = True
                result.status = "unavailable"
                result.reason += "; Containerende unbestätigt, Lauf gesperrt"
        return result
