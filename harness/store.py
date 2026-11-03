"""Ereignisse und Endbericht als begrenzte, lesbare JSON-Dateien speichern."""

from __future__ import annotations

import copy
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

from harness.process import MARKER


def clip(text: str, limit: int) -> tuple[str, bool]:
    """Bytegrenze inklusive Kürzungsmarker; keine halben UTF-8-Zeichen ausgeben."""
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text, False
    return data[: max(0, limit - len(MARKER.encode()))].decode("utf-8", "ignore") + MARKER, True


class RunStore:
    """Thread-sichere Ereignisse für UI und Datei, atomarer Bericht am Laufende.

    Budgetaufteilung: Hälfte für Ereignisse, je ein Viertel für Bericht und Diff.
    Die UI bekommt Kopien, damit sie keine laufenden Controllerdaten verändert.
    """

    def __init__(self, path: Path, artifact_bytes: int):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self.budget = artifact_bytes
        self.event_bytes = 0
        self.events_truncated = False
        self.events: list[dict] = []
        self.lock = threading.RLock()
        # S2-S: Nach Prozessneustart die vorhandenen begrenzten Ereignisse öffnen.
        events = path / "events.jsonl"
        if events.exists():
            if events.is_symlink() or events.stat().st_size > self.budget // 4:
                raise ValueError("Ungültiges Ereignisprotokoll")
            # Ein fremder inspect-Prozess kann während eines Appends lesen.
            # Eine noch nicht abgeschlossene letzte Zeile ist kein fertiges Ereignis.
            self.events = [
                json.loads(line)
                for line in events.read_text("utf-8").splitlines(keepends=True)
                if line.endswith("\n")
            ]
            self.event_bytes = events.stat().st_size
            self.events_truncated = any(e.get("kind") == "artifact_limit" for e in self.events)

    def event(self, kind: str, **data) -> None:
        with self.lock:
            event = {"at": datetime.now(UTC).isoformat(), "kind": kind, **data}
            line = json.dumps(event, ensure_ascii=False) + "\n"
            # Vier Viertel: Ereignisse, Bericht, Diff und atomarer Session-Checkpoint.
            if self.event_bytes + len(line.encode("utf-8")) > self.budget // 4 - 512:
                if self.events_truncated:
                    return
                self.events_truncated = True
                event = {
                    "at": event["at"],
                    "kind": "artifact_limit",
                    "message": "Ereignisprotokoll gekürzt",
                }
                line = json.dumps(event) + "\n"
            self.event_bytes += len(line.encode("utf-8"))
            self.events.append(event)
            # Keine Windows-CRLF-Erweiterung: Dateibytes entsprechen dem Bytebudget.
            with (self.path / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line)

    def snapshot(self) -> list[dict]:
        with self.lock:
            return copy.deepcopy(self.events)

    def report(self, report: dict) -> dict:
        value = copy.deepcopy(report)
        value["events_truncated"] = self.events_truncated
        # Status und Exit-Code bleiben erhalten, auch wenn Ausgabetext gekürzt wird.
        checks = value.get("checks", [])
        text_budget = max(256, (self.budget // 4 - 32768) // max(1, len(checks) * 2))
        for check in checks:
            check["reason"], reason_shortened = clip(check.get("reason", ""), 256)
            for key in ("stdout", "stderr"):
                check[key], shortened = clip(check.get(key, ""), text_budget)
                check["truncated"] = check.get("truncated", False) or shortened or reason_shortened
        data = json.dumps(value, ensure_ascii=False, indent=2)
        if len(data.encode("utf-8")) > self.budget // 4:
            # Sicherheitsreserve für kleine Budgets: Metadaten haben Vorrang vor Text.
            for check in checks:
                check["stdout"], check["stderr"], check["truncated"] = MARKER, MARKER, True
            value["report_truncated"] = True
            data = json.dumps(value, ensure_ascii=False, indent=2)
        # Auch ungewöhnlich lange Modell-Schrittmetadaten dürfen das Budget nicht
        # umgehen. Vollständige Schritte stehen im separat begrenzten Checkpoint.
        while len(data.encode("utf-8")) > self.budget // 4 and value.get("steps"):
            value["steps"].pop(0)
            value["steps_truncated"] = True
            data = json.dumps(value, ensure_ascii=False, indent=2)
        if len(data.encode("utf-8")) > self.budget // 4 and value.get("pending"):
            value["pending"] = {k: v for k, v in value["pending"].items() if k != "arguments"}
            value["pending_details"] = "session.json"
            data = json.dumps(value, ensure_ascii=False, indent=2)
        if len(data.encode("utf-8")) > self.budget // 4:
            raise ValueError("Berichtsmetadaten überschreiten Artefaktbudget")
        temporary = self.path / "report.tmp"
        temporary.write_text(data, "utf-8", newline="\n")
        temporary.replace(self.path / "report.json")
        return value
