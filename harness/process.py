"""Begrenztes Einlesen vertrauenswürdiger Git-/Docker-Prozesse.

Diese Funktion ist keine Sandbox. Zielcode darf nur über DockerRunner laufen.
Bei Timeout beendet capture den lokalen CLI-Prozess; DockerRunner muss danach
zusätzlich den Container samt Kindprozessen entfernen.
"""

from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass

MARKER = "\n[Ausgabe gekürzt]\n"


class BoundedOutput:
    """Ein gemeinsames Bytebudget für stdout und stderr, geschützt vor Threadrennen."""

    def __init__(self, limit: int):
        self.limit = limit
        self.data = {"stdout": bytearray(), "stderr": bytearray()}
        self.total = 0
        self.truncated = False
        self.lock = threading.Lock()

    def add(self, stream: str, chunk: bytes) -> None:
        with self.lock:
            room = max(0, self.limit - self.total)
            self.data[stream].extend(chunk[:room])
            self.total += min(room, len(chunk))
            self.truncated |= len(chunk) > room

    def text(self, stream: str) -> str:
        return self.data[stream].decode("utf-8", "replace")


@dataclass
class ProcessResult:
    """Rohbefund eines lokalen Befehls, unabhängig von seiner Textausgabe."""

    command: list[str]
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    timed_out: bool = False
    cancelled: bool = False
    seconds: float = 0


def capture(
    command: list[str],
    *,
    timeout: float = 15,
    limit: int = 65536,
    cancel: threading.Event | None = None,
    cwd=None,
) -> ProcessResult:
    started = time.monotonic()
    out = BoundedOutput(limit)
    process = subprocess.Popen(
        command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    def drain(pipe, channel):
        # Weiter lesen, auch wenn das Budget voll ist. Sonst könnte ein voller
        # Pipe-Puffer den Kindprozess blockieren. Keine readline()-Aufrufe:
        # auch eine einzige endlose Zeile muss begrenzt bleiben.
        try:
            while chunk := pipe.read1(4096):
                out.add(channel, chunk)
        finally:
            pipe.close()

    threads = [
        threading.Thread(target=drain, args=(pipe, channel), daemon=True)
        for pipe, channel in [(process.stdout, "stdout"), (process.stderr, "stderr")]
    ]
    for thread in threads:
        thread.start()
    timed_out = cancelled = False
    while process.poll() is None:
        cancelled = cancel is not None and cancel.is_set()
        timed_out = time.monotonic() - started >= timeout
        if cancelled or timed_out:
            process.kill()
            break
        time.sleep(0.03)
    process.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)
    return ProcessResult(
        command,
        process.returncode,
        out.text("stdout"),
        out.text("stderr"),
        out.truncated,
        timed_out,
        cancelled,
        time.monotonic() - started,
    )
