import os
import threading

import pytest

from harness.config import Limits
from harness.errors import Cancelled, ToolError
from harness.repository import RepositoryTools


@pytest.fixture
def tools(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "shopping_cart.py").write_text("alpha\nunique value\nalpha\n", "utf-8")
    (root / "db.py").write_text("protected\n", "utf-8")
    (root / "config.json").write_text('{"secret":"hidden"}', "utf-8")
    (root / "binary.bin").write_bytes(b"\x00\xff")
    return RepositoryTools(root, ["shopping_cart.py"], Limits(), lambda _: pytest.fail("unexpected check"), threading.Event())


def test_list_read_search_edit(tools):
    assert "shopping_cart.py" in tools.execute("list_files", {})["files"]
    assert "config.json" not in tools.execute("list_files", {})["files"]
    assert "2: unique value" in tools.execute("read_file", {"path": "shopping_cart.py"})["content"]
    assert tools.execute("search_files", {"query": "unique"})["matches"][0]["line"] == 2
    tools.execute("replace_text", {"path": "shopping_cart.py", "old": "unique value", "new": "changed"})
    assert "changed" in (tools.root / "shopping_cart.py").read_text()


@pytest.mark.parametrize("path", ["../outside.py", "/etc/passwd", "C:\\Windows\\win.ini", "C:relative", "\\\\server\\share",
                                 "..\\outside.py", "shopping_cart.py:stream", ".git/config", "config.json", "CON", "foo."])
def test_path_boundary(tools, path):
    before = (tools.root / "shopping_cart.py").read_bytes()
    with pytest.raises(ToolError):
        tools.execute("replace_text", {"path": path, "old": "alpha", "new": "damaged"})
    assert (tools.root / "shopping_cart.py").read_bytes() == before


def test_symlink_or_junction_escape(tools, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("unchanged")
    link = tools.root / "escape"
    if os.name == "nt":
        import subprocess
        result = subprocess.run(["powershell", "-NoProfile", "-Command",
            f"New-Item -ItemType Junction -Path '{link}' -Target '{outside}'"], capture_output=True)
        assert result.returncode == 0, result.stderr
    else:
        link.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(ToolError):
            tools.execute("read_file", {"path": "escape/secret.py"})
        assert "escape/secret.py" not in tools.execute("list_files", {})["files"]
        assert (outside / "secret.py").read_text() == "unchanged"
    finally:
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()


def test_conflict_protected_binary_and_size(tools):
    for old in ("alpha", "missing"):
        with pytest.raises(ToolError, match="genau einmal"):
            tools.execute("replace_text", {"path": "shopping_cart.py", "old": old, "new": "oops"})
    with pytest.raises(ToolError, match="Änderungsbereich"):
        tools.execute("replace_text", {"path": "db.py", "old": "protected", "new": "oops"})
    with pytest.raises(ToolError, match="Binär"):
        tools.execute("read_file", {"path": "binary.bin"})
    (tools.root / "large.py").write_bytes(b"a" * (tools.limits.file_bytes + 1))
    with pytest.raises(ToolError, match="Dateigrößenlimit"):
        tools.execute("read_file", {"path": "large.py"})


@pytest.mark.parametrize("name,args", [("shell", {}), ("read_file", {"path": 5}),
    ("list_files", {"extra": True}), ("read_file", {"path": "shopping_cart.py", "start_line": True}),
    ("replace_text", "{broken"), ("run_check", {"check_id": "whoami"})])
def test_invalid_requests_are_rejected(tools, name, args):
    with pytest.raises(ToolError):
        tools.execute(name, args)


def test_cancel_blocks_edits(tools):
    tools.cancel.set()
    with pytest.raises(Cancelled):
        tools.execute("replace_text", {"path": "shopping_cart.py", "old": "unique", "new": "wrong"})
    assert "unique" in (tools.root / "shopping_cart.py").read_text()
