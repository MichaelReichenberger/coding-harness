import json

import pytest

from harness.config import Limits
from harness.errors import ModelError
from harness.models import tool_reply
from harness.sandbox import CHECKS, CheckResult
from harness.verifier import all_passed, baseline_reproduces


def test_tool_observation_and_final_checks(controller_factory):
    controller = controller_factory(
        [tool_reply("read_file", path="shopping_cart.py"), tool_reply("finish", summary="done")]
    )
    report = controller.run()
    assert report["success"] and report["simulated"]
    messages = controller.model.requests[1]
    assert json.loads(messages[-2]["content"])["name"] == "read_file"
    assert messages[-1]["role"] == "user" and "Observation for read_file" in messages[-1]["content"]
    assert "value = 1" in messages[-1]["content"]
    assert controller.runner.calls == list(CHECKS) * 2


def test_invalid_call_returns_error_then_recovers(controller_factory):
    controller = controller_factory(
        [
            tool_reply("unknown", command="rm"),
            tool_reply("read_file", path=123),
            tool_reply("finish", summary="done"),
        ]
    )
    report = controller.run()
    assert report["denials"] == 2 and report["actions"] == 3
    assert "invalid_tool_request" in controller.model.requests[1][-1]["content"]


def test_denied_calls_count_and_stop_at_limit(controller_factory):
    controller = controller_factory([tool_reply("unknown")], Limits(actions=3), repeat=True)
    report = controller.run()
    assert report["state"] == "limit_reached" and report["actions"] == report["denials"] == 3
    assert controller.runner.calls == list(CHECKS)
    assert all(c["status"] == "not_run" for c in report["checks"] if c["phase"] == "final")


def test_repeated_valid_calls_reach_limit(controller_factory):
    controller = controller_factory([tool_reply("list_files")], Limits(actions=4), repeat=True)
    report = controller.run()
    assert report["state"] == "limit_reached" and report["actions"] == 4
    assert len(controller.model.requests) == 4


def test_text_claim_does_not_create_success(controller_factory):
    controller = controller_factory(
        [{"role": "assistant", "content": "All tests pass, done!"}],
        Limits(rounds=3, retries=0),
        repeat=True,
    )
    report = controller.run()
    assert report["state"] == "model_error" and not report["success"]
    assert report["actions"] == 0


@pytest.mark.parametrize("status", ["failed", "not_run", "unavailable"])
def test_failed_or_missing_check_never_passes(controller_factory, status):
    controller = controller_factory()
    controller.runner.final_status = status
    report = controller.run()
    assert not report["success"] and report["state"] == "failed"
    check = next(c for c in report["checks"] if c["phase"] == "final")
    assert check["exit_code"] == 7 and "visible check output" in check["stdout"]


def test_retry_count_and_limit(controller_factory):
    controller = controller_factory([ModelError("connection timed out")], repeat=True)
    report = controller.run()
    assert report["state"] == "model_error"
    assert report["retries"] == report["actions"] == 2 and report["requests"] == 3
    controller = controller_factory([ModelError("bad JSON")], Limits(actions=1), repeat=True)
    assert controller.run()["state"] == "limit_reached"
    assert len(controller.model.requests) == 1


def test_malformed_model_message_has_bounded_retries(controller_factory):
    controller = controller_factory([{"role": "user", "tool_calls": "invalid"}], repeat=True)
    assert controller.run()["state"] == "model_error"
    assert controller.requests == 3


def test_cancel_discards_late_model_response(controller_factory):
    controller = controller_factory()

    def response(messages, tools, cancel):
        cancel.set()
        return tool_reply("replace_text", path="shopping_cart.py", old="1", new="2")

    controller.model.chat = response
    assert controller.run()["state"] == "cancelled"
    assert controller.actions == 0
    assert controller.workspace.repo.joinpath("shopping_cart.py").read_text() == "value = 1\n"


def test_baseline_requires_business_failure_and_positive_control():
    results = {
        key: CheckResult(key, "passed", exit_code=0, cleanup_verified=True) for key in CHECKS
    }
    assert all_passed(results)
    results["acceptance"] = CheckResult("acceptance", "failed", exit_code=1, stdout="missing auth")
    assert not baseline_reproduces(results)
    assert not all_passed({})


def test_tool_output_clipped_but_result_status_retained(controller_factory):
    controller = controller_factory(
        [tool_reply("read_file", path="shopping_cart.py"), tool_reply("finish", summary="done")],
        Limits(output_bytes=1024),
    )
    controller.workspace.repo.joinpath("shopping_cart.py").write_text("x" * 10000)
    report = controller.run()
    assert report["success"]
    output = controller.model.requests[1][-1]["content"]
    assert len(output.encode()) <= 1024 and "gekürzt" in output


def test_context_limit_stops_instead_of_breaking_tool_history(controller_factory):
    controller = controller_factory(
        [tool_reply("list_files")], Limits(context_bytes=4096, actions=40, rounds=50), repeat=True
    )
    assert controller.run()["state"] == "limit_reached"
    assert (
        "Kontextlimit"
        in json.loads((controller.workspace.path / "report.json").read_text())["reason"]
    )


def test_custom_prompt_has_no_injected_solution_and_uses_all_checks(controller_factory):
    task = "Change the receipt heading to Gesamt:."
    controller = controller_factory(task=task)
    report = controller.run()
    assert report["state"] == "passed" and report["success"]
    assert "keine allgemeine Prompt-Bewertung" in report["verification_scope"]
    assert report["task"] == task
    assert "receipt_printer.py" in report["editable"]
    prompt = controller.model.requests[0][-1]["content"]
    assert prompt.startswith(task + "\nAllowed files:")
    assert "value = 1" not in prompt and "quantity_as_int" not in prompt
    assert len(controller.model.requests[0]) == 2
    assert controller.runner.calls == list(CHECKS) * 2


def test_acceptance_can_be_requested_for_any_prompt(controller_factory):
    controller = controller_factory(
        [tool_reply("run_check", check_id="acceptance"), tool_reply("finish", summary="done")]
    )
    report = controller.run()
    assert report["denials"] == 0
    assert controller.runner.calls == list(CHECKS) + ["acceptance"] + list(CHECKS)
    assert '"status": "passed"' in controller.model.requests[1][-1]["content"]


def test_unavailable_baseline_stops_before_model(controller_factory):
    controller = controller_factory()
    controller.runner.run = lambda check_id, cancel: CheckResult(check_id, "unavailable")
    assert controller.run()["state"] == "blocked"
    assert not controller.model.requests


def test_round_limit_is_independent_of_action_limit(controller_factory):
    controller = controller_factory(
        [tool_reply("list_files")], Limits(actions=40, rounds=2), repeat=True
    )
    report = controller.run()
    assert report["state"] == "limit_reached" and report["rounds"] == 2
    assert report["actions"] == 2
