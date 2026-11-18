"""Führt geschützte Checks aus und bewertet ausschließlich deren Ergebnisse."""

from __future__ import annotations

import json
import threading

from harness.sandbox import CHECKS, FEATURE_CHECKS, CheckResult


def acceptance_evidence(result: CheckResult) -> dict:
    """Liest den maschinenlesbaren Befund des Belegdruck-Tests für den Bericht."""
    for line in reversed(result.stdout.splitlines()):
        if line.startswith("HARNESS_ACCEPTANCE="):
            try:
                return json.loads(line.split("=", 1)[1])
            except ValueError:
                return {}
    return {}


def baseline_reproduces(results: dict[str, CheckResult]) -> bool:
    """PDF-Nachweis: fachlicher Fehler statt fehlender Bibliothek oder kaputter Tests.

    Dies beschreibt unseren ausgewählten Akzeptanztest, keine Lösungsvorgabe.
    Der Controller verwendet es nur für den Bericht, nicht zum Steuern des Modells.
    """
    acceptance = results.get("acceptance", CheckResult("acceptance"))
    evidence = acceptance_evidence(acceptance)
    return (
        acceptance.status == "failed"
        and acceptance.exit_code == 1
        and not acceptance.timed_out
        and not acceptance.cancelled
        and acceptance.cleanup_verified
        and evidence.get("positive_control") is True
        and not evidence.get("infrastructure_errors", ["missing"])
        and set(evidence.get("business_failures", [])) == {"each_2", "each_3", "each_5"}
        and all_passed(results, [check_id for check_id in CHECKS if check_id != "acceptance"])
    )


def all_passed(results: dict[str, CheckResult], checks=CHECKS) -> bool:
    """Fehlender Check, Timeout oder unbestätigtes Containerende verhindert Erfolg."""
    return all(
        c in results
        and results[c].status == "passed"
        and results[c].exit_code == 0
        and not results[c].timed_out
        and not results[c].cancelled
        and results[c].cleanup_verified
        for c in checks
    )


def feature_baseline_reproduces(results):
    """S2-F: Fehlende Gebühren-API bei intakten Legacy-Kontrollen und Regressionen."""
    if set(results) != set(FEATURE_CHECKS):
        return False
    result = results.get("feature", CheckResult("feature"))
    for line in result.stdout.splitlines():
        if line.startswith("HARNESS_FEATURE="):
            try:
                evidence = json.loads(line.split("=", 1)[1])
            except ValueError:
                return False
            return (
                result.status == "failed"
                and result.exit_code == 1
                and result.cleanup_verified
                and not result.timed_out
                and not result.cancelled
                and evidence.get("positive_control") is True
                and bool(evidence.get("feature_failures"))
                and evidence.get("infrastructure_errors") == []
                and all_passed(
                    results, [check_id for check_id in FEATURE_CHECKS if check_id != "feature"]
                )
            )
    return False


class Verifier:
    """Einheitlicher Aufruf für Baseline, Modell-Check und unabhängige Endprüfung."""

    def __init__(self, runner, store, cancel: threading.Event):
        self.runner, self.store, self.cancel = runner, store, cancel
        self.records: list[dict] = []
        self.checks = getattr(runner, "checks", CHECKS)

    def check(self, check_id: str, phase: str) -> CheckResult:
        result = self.runner.run(check_id, self.cancel)
        record = {"phase": phase, **result.to_dict()}
        self.records.append(record)
        self.store.event("check", **record)
        return result

    def with_not_run(self) -> list[dict]:
        records = list(self.records)
        for phase in ("baseline", "final"):
            for check_id in self.checks:
                if not any(r["phase"] == phase and r["check_id"] == check_id for r in records):
                    records.append({"phase": phase, **CheckResult(check_id).to_dict()})
        return records
