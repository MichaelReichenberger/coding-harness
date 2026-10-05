from __future__ import annotations

import argparse
import json
import sys

from harness.config import ROOT, load_settings, load_target
from harness.doctor import doctor
from harness.process import capture
from harness.service import RunService
from harness.workspace import prepare_reference


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Supermarket Coding Harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Umgebung und externe Voraussetzungen prüfen")
    setup = sub.add_parser("setup", help="Fixierte Referenz beziehen, optional Sandbox-Image bauen")
    setup.add_argument("--build", action="store_true")
    run = sub.add_parser("run", help="Neuer Lauf vom fixierten Commit")
    run.add_argument("--provider", choices=["ollama", "scripted"], default="ollama")
    run.add_argument("--task")
    sub.add_parser("baseline", help="Nur unveränderten Ausgangszustand prüfen")
    args = parser.parse_args()
    settings = load_settings()
    if args.command == "doctor":
        result = doctor(settings)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["live_ready"] else 2
    if args.command == "setup":
        prepare_reference(load_target(), ROOT / ".harness/reference/supermarket-receipt")
        print("Supermarket-Commit vorhanden:", load_target().commit)
        if args.build:
            result = capture(["docker", "build", "--tag", settings.image, str(ROOT / "sandbox")],
                             timeout=600, limit=262144)
            print(result.stdout, result.stderr)
            return 0 if result.exit_code == 0 and not result.timed_out else 2
        return 0
    service = RunService(settings)
    baseline = args.command == "baseline"
    target = load_target()
    service.start(target.task if baseline else args.task or target.task,
                  "scripted" if baseline else args.provider, baseline_only=baseline)
    print("Lauf:", service.workspace.run_id, flush=True)
    seen = 0
    try:
        while service.active:
            events = service.store.snapshot()
            for event in events[seen:]:
                if event["kind"] in {"state", "check", "tool", "model_request", "model_error"}:
                    print(event["kind"], event.get("state", event.get("check_id", event.get("name", ""))),
                          event.get("status", ""), flush=True)
            seen = len(events)
            service.thread.join(timeout=0.25)
    except KeyboardInterrupt:
        service.cancel()
        print("Abbruch angefordert; Containerende wird geprüft.", flush=True)
        service.thread.join()
    report = service.report
    print(json.dumps({"state": report["state"], "reason": report["reason"],
                      "report": str(service.workspace.path / "report.json")}, ensure_ascii=False))
    return 0 if report["success"] or baseline and report["state"] == "baseline_reproduced" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Harness-Fehler: {exc}", file=sys.stderr)
        sys.exit(2)
