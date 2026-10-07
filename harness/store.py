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

    def event(self, kind: str, **data) -> None:
        with self.lock:
            event = {"at": datetime.now(UTC).isoformat(), "kind": kind, **data}
            line = json.dumps(event, ensure_ascii=False) + "\n"
            if self.event_bytes + len(line.encode("utf-8")) > self.budget // 2 - 512:
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
            with (self.path / "events.jsonl").open("a", encoding="utf-8") as stream:
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
            for key in ("stdout", "stderr"):
                check[key], shortened = clip(check.get(key, ""), text_budget)
                check["truncated"] = check.get("truncated", False) or shortened
        data = json.dumps(value, ensure_ascii=False, indent=2)
        if len(data.encode("utf-8")) > self.budget // 4:
            # Sicherheitsreserve für kleine Budgets: Metadaten haben Vorrang vor Text.
            for check in checks:
                check["stdout"], check["stderr"], check["truncated"] = MARKER, MARKER, True
            value["report_truncated"] = True
            data = json.dumps(value, ensure_ascii=False, indent=2)
        temporary = self.path / "report.tmp"
        temporary.write_text(data, "utf-8")
        temporary.replace(self.path / "report.json")
        return value
