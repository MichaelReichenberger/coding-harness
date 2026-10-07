import threading

import pytest

from harness.config import Limits
from harness.errors import SandboxError
from harness.sandbox import DockerRunner


def test_trusted_file_integrity_checked_before_execution(tmp_path):
    repo, trusted = tmp_path / "repo", tmp_path / "checks"
    repo.mkdir()
    trusted.mkdir()
    test = trusted / "acceptance.py"
    test.write_text("original")
    runner = DockerRunner(repo, trusted, "image", "test", Limits())
    test.write_text("changed")
    with pytest.raises(SandboxError, match="Integrität"):
        runner.run("acceptance", threading.Event())


def test_poisoned_runner_and_unknown_checks_never_execute(tmp_path):
    runner = DockerRunner(tmp_path, tmp_path, "image", "test", Limits())
    with pytest.raises(SandboxError, match="Unbekannte"):
        runner.run("arbitrary-shell", threading.Event())
    runner.poisoned = True
    with pytest.raises(SandboxError, match="Containerende"):
        runner.run("acceptance", threading.Event())


def test_container_command_has_no_host_credentials_or_shell(tmp_path):
    runner = DockerRunner(tmp_path / "repo", tmp_path / "checks", "image", "test", Limits())
    command = runner.create_command(
        "owned-container", ["python", "/trusted/entry.py", "acceptance"]
    )
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--user") + 1] == "10001:10001"
    assert "--read-only" in command and "--privileged" not in command
    assert not any("docker.sock" in s or "SSH" in s for s in command)
    mounts = [command[i + 1] for i, arg in enumerate(command) if arg == "--mount"]
    assert len(mounts) == 2 and all(m.endswith(",readonly") for m in mounts)
