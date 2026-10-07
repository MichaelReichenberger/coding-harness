import sys

from harness.process import capture


def test_newlineless_output_bounded_during_capture():
    result = capture(
        [sys.executable, "-c", "import os; os.write(1,b'x'*2000000); os.write(2,b'e'*1000000)"],
        limit=4096,
    )
    assert result.exit_code == 0 and result.truncated
    assert len(result.stdout.encode()) + len(result.stderr.encode()) <= 4096


def test_nonzero_and_timeout():
    result = capture([sys.executable, "-c", "import sys; print('failed'); sys.exit(7)"])
    assert result.exit_code == 7 and "failed" in result.stdout
    result = capture([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.2)
    assert result.timed_out and result.seconds < 5
