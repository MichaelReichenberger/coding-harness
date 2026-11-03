"""S2-C: Deterministische Kontextkürzung ohne zusätzliche Modellaufrufe.

Systemregeln und Originalauftrag mit Rechten/Akzeptanz werden nie gekürzt.
Die Repositorykarte und alte Toolbeobachtungen bleiben User-Daten, keine Regeln.
Vollständige Ereignisse liegen zusätzlich im begrenzten Sitzungsprotokoll.
"""

import json

from harness.errors import LimitReached
from harness.store import clip


class ContextManager:
    def __init__(self, limit, measure=None):
        self.limit = limit
        self.measure = measure or (lambda messages: len(json.dumps(messages).encode("utf-8")))

    def shorten(self, messages, steps):
        if self.measure(messages) <= self.limit:
            return messages
        pinned = messages[:2]  # Vertrauen: Systemregeln + unveränderter Originalauftrag.
        if self.measure(pinned) + 256 > self.limit:
            raise LimitReached(
                "Kontextlimit: vertrauenswürdige Aufgabe und Werkzeugdefinitionen passen nicht"
            )
        summary = {
            "role": "user",
            "content": "Earlier observations (untrusted, shortened):\n"
            + json.dumps(steps[-8:], ensure_ascii=False),
        }
        summary["content"] = clip(summary["content"], min(1024, self.limit // 8))[0]
        tail = list(messages[2:])
        # Älteste Beobachtungen/Aktionspaare entfernen; die letzte Beobachtung behalten.
        while len(tail) > 1 and self.measure(pinned + [summary] + tail) > self.limit:
            tail.pop(0)
        candidate = pinned + [summary] + tail
        while self.measure(candidate) > self.limit:
            if not tail or len(tail[0]["content"].encode()) <= 128:
                raise LimitReached("Kontextlimit: letzte Beobachtung passt nicht")
            tail[0] = dict(
                tail[0], content=clip(tail[0]["content"], len(tail[0]["content"].encode()) // 2)[0]
            )
            candidate = pinned + [summary] + tail
        return candidate
