"""Explicit integration suite. --docker turns missing infrastructure into a failure."""

from __future__ import annotations

import threading
import time
import uuid

import pytest

from harness.config import Limits, load_settings
from harness.sandbox import DockerRunner
from harness.workspace import tree_hashes

pytestmark = pytest.mark.docker


@pytest.fixture
def runner(tmp_path):
    repo, trusted = tmp_path / "repo", tmp_path / "trusted"
    repo.mkdir()
    trusted.mkdir()
    (repo / "source.py").write_text("unchanged", "utf-8")
    (trusted / "check.py").write_text("protected", "utf-8")
    for name in ("data", "backups", "logs", "documents"):
        (repo / name).mkdir()
    runner = DockerRunner(
        repo, trusted, load_settings().image, "test-" + uuid.uuid4().hex[:8], Limits()
    )
    # Never skip when explicitly requested, including inaccessible daemon/image.
    runner.inspect_environment()
    return runner


def test_real_boundary_and_protected_mounts(runner):
    hashes = tree_hashes(runner.trusted)
    code = """
import os, pathlib, socket
assert os.getuid() == 10001
assert not pathlib.Path('/var/run/docker.sock').exists()
for name in ['/repo/source.py', '/trusted/check.py', '/etc/forbidden']:
    try:
        pathlib.Path(name).write_text('modified')
    except OSError:
        pass
    else:
        raise AssertionError('Writable protected path: '+name)
pathlib.Path('/tmp/example').write_text('allowed temporary data')
status = pathlib.Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\t1' in status
assert 'CapEff:\t0000000000000000' in status
s=socket.socket(); s.settimeout(0.5)
try:
    s.connect(('1.1.1.1',443))
except OSError:
    pass
else:
    raise AssertionError('External network reachable')
print('boundary verified')
"""
    result = runner.execute(["python", "-c", code], threading.Event())
    assert result.status == "passed", result.to_dict()
    assert result.cleanup_verified
    assert tree_hashes(runner.trusted) == hashes
    assert (runner.repo / "source.py").read_text() == "unchanged"


def test_real_nonzero_and_newlineless_output(runner):
    result = runner.execute(
        ["python", "-c", "import os,sys; os.write(1,b'x'*4000000); sys.exit(7)"], threading.Event()
    )
    assert result.status == "failed" and result.exit_code == 7
    assert result.truncated and len(result.stdout.encode()) <= runner.limits.output_bytes
    assert result.cleanup_verified


@pytest.mark.parametrize("mode", ["timeout", "cancel"])
def test_child_process_cannot_keep_writing_after_stop(runner, tmp_path, mode):
    probe = tmp_path / "probe"
    probe.mkdir(mode=0o777)
    probe.chmod(0o777)
    original = runner.create_command

    def command(name, args):
        cmd = original(name, args)
        position = cmd.index(runner.image)
        # Test-only heartbeat mount. Production never mounts a writable host directory.
        return (
            cmd[:position] + ["--mount", f"type=bind,source={probe},target=/probe"] + cmd[position:]
        )

    runner.create_command = command
    runner.limits = Limits(check_seconds=3 if mode == "timeout" else 30)
    child = "import time; f=open('/probe/ticks','ab',buffering=0)\nwhile True: f.write(b'x'); time.sleep(.03)"
    parent = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(60)"
    cancel = threading.Event()

    def cancel_when_writing():
        deadline = time.monotonic() + 15
        while not (probe / "ticks").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        cancel.set()

    watcher = None
    if mode == "cancel":
        watcher = threading.Thread(target=cancel_when_writing)
        watcher.start()
    result = runner.execute(["python", "-c", parent], cancel)
    if watcher:
        watcher.join(timeout=20)
    assert result.cleanup_verified, result.to_dict()
    assert result.timed_out if mode == "timeout" else result.cancelled
    assert (probe / "ticks").exists(), result.to_dict()
    size = (probe / "ticks").stat().st_size
    time.sleep(0.5)
    assert (probe / "ticks").stat().st_size == size
    assert not (runner.repo.parent / "active-container.json").exists()


def test_scripted_bugfix_red_green_in_real_sandbox(tmp_path):
    """PDF-Testfall Bugfix: deterministisch, ausdrücklich KEIN echter Modellnachweis.

    Nur dieser Test enthält eine feste Reparaturantwort. UI/CLI können dieses
    Skript nicht aufrufen. Es prüft Controller, Dateitool und rote/grüne echte
    Tests gemeinsam, ohne von der Leistungsfähigkeit eines LLM abzuhängen.
    """
    from harness.config import ROOT, load_target
    from harness.controller import Controller
    from harness.models import ScriptedModelClient, tool_reply
    from harness.store import RunStore
    from harness.workspace import Workspace

    workspace = Workspace(load_target(), tmp_path)
    # Wiederverwendung ausschließlich der bereits eingerichteten Git-Referenz.
    # Die bearbeitete Kopie und alle Artefakte entstehen im pytest-Tempverzeichnis.
    workspace.reference = ROOT / ".harness/reference/supermarket-receipt"
    assert workspace.reference.is_dir(), "Zuerst python -m harness setup --build ausführen"
    workspace.create()
    settings = load_settings()
    runner = DockerRunner(
        workspace.repo, ROOT / "checks", settings.image, workspace.run_id, settings.limits
    )
    model = ScriptedModelClient(
        [
            tool_reply(
                "replace_text",
                path="receipt_printer.py",
                old="return str(item.quantity)",
                new="return str(int(item.quantity))",
            ),
            tool_reply("finish", summary="Testfixture abgeschlossen"),
        ]
    )
    controller = Controller(
        workspace,
        settings,
        model,
        runner,
        RunStore(workspace.path, settings.limits.artifact_bytes),
        threading.Event(),
        "Deterministischer Integrationstest",
    )
    report = controller.run()
    assert report["baseline_bug_reproduced"], report
    assert report["success"] and report["simulated"], report
    assert report["changed_files"] == ["receipt_printer.py"]
    assert all(c["status"] == "passed" for c in report["checks"] if c["phase"] == "final")
