from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import pytest

from harness.config import Limits, Settings, load_target
from harness.controller import Controller
from harness.models import ScriptedModelClient, tool_reply
from harness.sandbox import CheckResult
from harness.store import RunStore


def pytest_addoption(parser):
    parser.addoption(
        "--docker",
        action="store_true",
        help="Run real Docker boundary tests; unavailable = failure",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--docker"):
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Docker integration explicitly disabled; use --docker")
                )


def baseline_failure():
    return CheckResult(
        "acceptance",
        "failed",
        exit_code=1,
        cleanup_verified=True,
        stdout="HARNESS_ACCEPTANCE="
        + json.dumps(
            {
                "positive_control": True,
                "infrastructure_errors": [],
                "business_failures": ["each_2", "each_3", "each_5"],
            }
        ),
    )


class FakeRunner:
    """Explicit deterministic double; no target application code is ever imported on the host."""

    def __init__(self):
        self.gate = threading.RLock()
        self.hashes = {"acceptance.py": "fake-test-digest"}
        self.poisoned = False
        self.calls = []
        self.final_status = "passed"
        self.baseline_count = 3

    def inspect_environment(self):
        return {"test_double": True}

    def run(self, check_id, cancel):
        self.calls.append(check_id)
        if len(self.calls) == 1 and check_id == "acceptance":
            return baseline_failure()
        status = "passed" if len(self.calls) <= self.baseline_count else self.final_status
        return CheckResult(
            check_id,
            status,
            command=["fake-check", check_id],
            exit_code=0 if status == "passed" else 7,
            stdout="visible check output",
            cleanup_verified=True,
        )


@pytest.fixture
def controller_factory(tmp_path):
    count = 0

    def create(replies=None, limits=None, repeat=False, task="Eine frei eingegebene Testaufgabe"):
        nonlocal count
        count += 1
        run_path = tmp_path / str(count)
        repo = run_path / "repo"
        repo.mkdir(parents=True)
        (repo / "shopping_cart.py").write_text("value = 1\n", "utf-8")
        (repo / "app.py").write_text("app = 'example'\n", "utf-8")
        workspace = SimpleNamespace(
            repo=repo,
            path=run_path,
            run_id=f"test-{count}",
            target=load_target(),
            diff=lambda limit: ("", [], False),
        )
        settings = Settings(limits=limits or Limits())
        model = ScriptedModelClient(
            replies or [tool_reply("finish", summary="done")], repeat=repeat
        )
        runner = FakeRunner()
        controller = Controller(
            workspace,
            settings,
            model,
            runner,
            RunStore(run_path, settings.limits.artifact_bytes),
            threading.Event(),
            task,
        )
        return controller

    return create
