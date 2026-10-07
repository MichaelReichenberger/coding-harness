import pytest

from harness.config import Settings, load_target
from harness.errors import HarnessError
from harness.store import RunStore
from harness.workspace import RunLock, Workspace


def test_os_lock_prevents_two_runs(tmp_path):
    lock = RunLock(tmp_path)
    try:
        with pytest.raises(HarnessError, match="bereits aktiv"):
            RunLock(tmp_path)
    finally:
        lock.close()
    RunLock(tmp_path).close()


def test_diff_includes_new_deleted_and_missing_final_newline(tmp_path):
    workspace = Workspace(load_target(), tmp_path)
    workspace.base.mkdir(parents=True)
    workspace.repo.mkdir()
    (workspace.base / "deleted.py").write_text("old\n")
    (workspace.repo / "added.py").write_text("new")
    diff, files, truncated = workspace.diff()
    assert files == ["added.py", "deleted.py"] and not truncated
    assert "new file mode" in diff and "deleted file mode" in diff
    assert "/dev/null" in diff and "No newline at end of file" in diff


def test_event_storage_bounded_and_status_retained(tmp_path):
    store = RunStore(tmp_path, 65536)
    for _ in range(100):
        store.event("large", output="x" * 5000)
    result = store.report(
        {"success": False, "checks": [{"status": "failed", "exit_code": 9, "stdout": "x" * 100000}]}
    )
    assert result["checks"][0]["exit_code"] == 9 and result["checks"][0]["truncated"]
    assert result["events_truncated"]
    assert sum(p.stat().st_size for p in tmp_path.iterdir()) < 65536


def test_configuration_rejects_unknown_keys_and_unsafe_url():
    with pytest.raises(ValueError):
        Settings.model_validate({"shell": "cmd"})
    with pytest.raises(ValueError):
        Settings(ollama_base_url="http://secret:password@localhost:11434")
