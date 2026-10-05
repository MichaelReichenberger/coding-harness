from __future__ import annotations

import json
import threading

from harness.errors import Cancelled, HarnessError
from harness.sandbox import CHECKS, CheckResult


def acceptance_evidence(result: CheckResult) -> dict:
    for line in reversed(result.stdout.splitlines()):
        if line.startswith("HARNESS_ACCEPTANCE="):
            try:
                return json.loads(line.split("=", 1)[1])
            except ValueError:
                return {}
    return {}


def baseline_reproduces(results: dict[str, CheckResult]) -> bool:
    acceptance = results.get("acceptance", CheckResult("acceptance"))
    evidence = acceptance_evidence(acceptance)
    return (acceptance.status == "failed" and acceptance.exit_code == 1
            and not acceptance.timed_out and not acceptance.cancelled
            and acceptance.cleanup_verified
            and evidence.get("positive_control") is True
            and not evidence.get("infrastructure_errors", ["missing"])
            and set(evidence.get("business_failures", [])) == {"odd_3", "odd_5", "odd_7"}
            and all(results.get(c, CheckResult(c)).status == "passed"
                    and results[c].exit_code == 0 and results[c].cleanup_verified
                    and not results[c].timed_out and not results[c].cancelled
                    for c in CHECKS if c != "acceptance"))


def all_passed(results: dict[str, CheckResult]) -> bool:
    return all(c in results and results[c].status == "passed" and results[c].exit_code == 0
               and not results[c].timed_out and not results[c].cancelled
               and results[c].cleanup_verified for c in CHECKS)


class Verifier:
    def __init__(self, runner, store, cancel: threading.Event):
        self.runner, self.store, self.cancel = runner, store, cancel
        self.records: list[dict] = []

    def check(self, check_id: str, phase: str) -> CheckResult:
        result = self.runner.run(check_id, self.cancel)
        record = {"phase": phase, **result.to_dict()}
        self.records.append(record)
        self.store.event("check", **record)
        if self.runner.poisoned:
            raise HarnessError("Containerende unbestätigt; Lauf blockiert")
        if self.cancel.is_set() or result.cancelled:
            raise Cancelled("Abbruch während der Prüfung")
        return result

    def suite(self, phase: str) -> dict[str, CheckResult]:
        results = {}
        for check_id in CHECKS:
            if self.cancel.is_set():
                raise Cancelled("Abbruch angefordert")
            results[check_id] = self.check(check_id, phase)
        return results

    def with_not_run(self) -> list[dict]:
        records = list(self.records)
        for phase in ("baseline", "final"):
            for check_id in CHECKS:
                if not any(r["phase"] == phase and r["check_id"] == check_id for r in records):
                    records.append({"phase": phase, **CheckResult(check_id).to_dict()})
        return records
