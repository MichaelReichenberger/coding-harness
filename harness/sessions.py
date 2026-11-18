"""S2-S/T: Atomare Checkpoints außerhalb des editierbaren Repositorys.

Vor Aktionen wird pending gespeichert, danach der neue Dateizustand. Stirbt das
Programm dazwischen, wird die Aktion beim Öffnen als unsicher angezeigt. Resume
führt sie niemals erneut aus. Die Dateien sind lokale Einbenutzer-Daten, kein
signiertes Mehrbenutzerformat; Agententools besitzen keinen Zugriff auf sie.
"""

import hashlib
import json
import os
import re
from pathlib import Path

from harness.errors import HarnessError


def checked_hashes(root):
    """Auch eigene Edits, neue Dateien und Link-Manipulationen revalidieren."""
    if root.is_symlink() or root.is_junction() or not root.is_dir():
        raise HarnessError("Unsicheres Arbeitsverzeichnis")
    result = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise HarnessError("Link im gespeicherten Arbeitszustand")
        if path.is_file():
            size = path.stat().st_size
            total += size
            if path.stat().st_nlink > 1 or size > 1048576 or total > 40 * 1024 * 1024:
                raise HarnessError("Arbeitszustand überschreitet Datei-/Größengrenzen")
            result[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


class SessionStore:
    def __init__(self, home, run_id, budget):
        if not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", run_id):
            raise HarnessError("Ungültige Sitzungs-ID")
        self.path = Path(home) / "runs" / run_id
        for parent in (self.path.parent, self.path):
            if parent.is_symlink() or parent.is_junction():
                raise HarnessError("Sitzungspfad ist ein Link")
        self.budget = budget // 4

    def write(self, data):
        data = dict(data, schema=2)
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        if len(encoded) > self.budget:
            raise HarnessError(
                "Checkpoint überschreitet Artefaktbudget; sichere Fortsetzung pausiert"
            )
        self.path.mkdir(parents=True, exist_ok=True)
        temporary = self.path / "session.tmp"
        with temporary.open("wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path / "session.json")

    def load(self):
        path = self.path / "session.json"
        if path.is_symlink() or path.stat().st_size > self.budget:
            raise HarnessError("Unsichere oder zu große Sitzungsdatei")
        data = json.loads(path.read_text("utf-8"))
        if data.get("schema") != 2:
            raise HarnessError("Unbekanntes Sitzungsformat")
        return data

    def cancel(self):
        if not self.path.is_dir():
            raise HarnessError("Sitzung existiert nicht")
        (self.path / "cancel.request").touch()

    def pause(self, reason):
        (self.path / "pause.json").write_text(
            json.dumps({"state": "paused", "reason": str(reason)[:2000]}), "utf-8"
        )

    def validate(self, workspace, policy):
        data = self.load()
        # Ein fertiger Lauf bleibt abgeschlossen, auch wenn Resume angefragt wird.
        if data["state"] in {"passed", "baseline_checked"}:
            raise HarnessError("Abgeschlossene Sitzung benötigt keine Fortsetzung")
        try:
            if data["policy"] != policy:
                raise HarnessError("Berechtigungen, Checks oder Einstellungen wurden geändert")
            if data.get("pending") is not None:
                raise HarnessError(
                    "Unsichere unterbrochene Aktion: keine automatische Wiederholung"
                )
            if (workspace.path / "active-container.json").exists():
                raise HarnessError("Containerende ist unbestätigt")
            if (
                checked_hashes(workspace.repo) != data["repo_hashes"]
                or checked_hashes(workspace.base) != data["base_hashes"]
            ):
                raise HarnessError("Arbeitskopie oder Baseline weicht vom Checkpoint ab")
            for name in ("actions", "rounds", "requests", "retries", "denials"):
                if type(data[name]) is not int or data[name] < 0:
                    raise HarnessError("Ungültige gespeicherte Zähler")
            limits = policy["settings"]["limits"]
            if data["actions"] >= limits["actions"] or data["rounds"] >= limits["rounds"]:
                raise HarnessError("Gespeicherte Limits sind verbraucht")
            return data
        except (HarnessError, KeyError) as exc:
            self.pause(exc)
            raise HarnessError("Sitzung pausiert: " + str(exc)) from exc
