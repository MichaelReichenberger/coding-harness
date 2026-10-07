"""Fixierter Quellstand, wegwerfbare Laufkopie, Diff und prozessübergreifende Sperre.

Keine Git-Änderung des Nutzers wird zurückgesetzt. git archive liest ausschließlich
den versionierten Commit in der Referenz. repo wird bearbeitet, base bleibt als
Vergleichskopie bestehen. Das Modell sieht weder base noch den Git-Referenzbereich.
"""

from __future__ import annotations

import difflib
import hashlib
import io
import os
import shutil
import stat
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from harness.config import ROOT, Target
from harness.errors import HarnessError
from harness.process import capture


def git_args(repo: Path, *args: str) -> list[str]:
    # Gilt nur für diesen Befehl und diese Kopie, nie für die globale Git-Konfiguration.
    return [
        "git",
        "-c",
        f"safe.directory={repo.resolve().as_posix()}",
        "-c",
        "core.autocrlf=false",
        "-C",
        str(repo),
        *args,
    ]


def require_git(repo: Path, *args: str) -> str:
    result = capture(git_args(repo, *args), timeout=60)
    if result.exit_code or result.timed_out:
        raise HarnessError(result.stderr or "Git fehlgeschlagen")
    return result.stdout.strip()


def prepare_reference(target: Target, reference: Path) -> None:
    """Bei Bedarf klonen; URL und tatsächlichen Commit vor Verwendung prüfen."""
    if not reference.exists():
        reference.parent.mkdir(parents=True, exist_ok=True)
        result = capture(["git", "clone", "--no-checkout", target.url, str(reference)], timeout=180)
        if result.exit_code or result.timed_out:
            raise HarnessError(result.stderr or "Klonen fehlgeschlagen")
    if require_git(reference, "remote", "get-url", "origin").removesuffix(".git") != target.url:
        raise HarnessError("Referenzkopie gehört nicht zum festgelegten Ziel-Repository")
    actual = require_git(reference, "rev-parse", f"{target.commit}^{{commit}}")
    if actual != target.commit:
        raise HarnessError("Ausgangs-Commit fehlt")


def export_commit(reference: Path, commit: str, destination: Path, subdirectory: str = "") -> None:
    # Kein Checkout mit lokalen Änderungen: nur die Bytes des festgelegten Commits.
    archive = destination.parent / "source.zip"
    tree = f"{commit}:{subdirectory}" if subdirectory else commit
    result = capture(
        git_args(reference, "archive", "--format=zip", f"--output={archive}", tree), timeout=30
    )
    if result.exit_code or result.timed_out:
        raise HarnessError(result.stderr or "Export fehlgeschlagen")
    try:
        if archive.stat().st_size > 20 * 1024 * 1024:
            raise HarnessError("Repository-Archiv überschreitet 20 MiB")
        with zipfile.ZipFile(archive) as source:
            # Auch ein öffentliches Repository ist untrusted. Archive dürfen keine
            # Pfadausbrüche/Symlinks oder unbegrenzt große Inhalte einschleusen.
            if sum(i.file_size for i in source.infolist()) > 40 * 1024 * 1024:
                raise HarnessError("Repository überschreitet 40 MiB")
            for entry in source.infolist():
                path = PurePosixPath(entry.filename)
                mode = entry.external_attr >> 16
                if path.is_absolute() or ".." in path.parts or "\\" in entry.filename:
                    raise HarnessError("Unsicherer Archivpfad")
                if stat.S_ISLNK(mode):
                    raise HarnessError("Symlinks im Zielarchiv sind nicht erlaubt")
                if any(p.lower() in {".git", ".env", "config_local.json"} for p in path.parts):
                    continue
                resolved = destination.joinpath(*path.parts)
                if entry.is_dir():
                    resolved.mkdir(parents=True, exist_ok=True)
                else:
                    resolved.parent.mkdir(parents=True, exist_ok=True)
                    resolved.write_bytes(source.read(entry))
    finally:
        archive.unlink(missing_ok=True)


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


class Workspace:
    """Ordner und Ausgangsstand eines einzigen Laufs, inklusive vollständigem Diff."""

    def __init__(self, target: Target, home: Path | None = None):
        self.target = target
        self.home = (home or ROOT / ".harness").resolve()
        self.reference = self.home / "reference/supermarket-receipt"
        self.run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        self.path = self.home / "runs" / self.run_id
        self.repo = self.path / "repo"
        self.base = self.path / "base"

    def create(self) -> None:
        prepare_reference(self.target, self.reference)
        self.path.mkdir(parents=True, exist_ok=True)
        export_commit(self.reference, self.target.commit, self.repo, self.target.subdirectory)
        shutil.copytree(self.repo, self.base)

    def diff(self, limit: int = 2 * 1024 * 1024) -> tuple[str, list[str], bool]:
        """Dateilisten bleiben vollständig; nur der Difftext kann gekürzt werden."""
        before, after = tree_hashes(self.base), tree_hashes(self.repo)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        output = io.StringIO()
        for name in changed:
            old, new = self.base / name, self.repo / name
            output.write(f"diff --git a/{name} b/{name}\n")
            if not old.exists():
                output.write("new file mode 100644\n")
            if not new.exists():
                output.write("deleted file mode 100644\n")
            a = old.read_text("utf-8").splitlines(keepends=True) if old.exists() else []
            b = new.read_text("utf-8").splitlines(keepends=True) if new.exists() else []
            for line in difflib.unified_diff(
                a,
                b,
                fromfile=f"a/{name}" if old.exists() else "/dev/null",
                tofile=f"b/{name}" if new.exists() else "/dev/null",
            ):
                output.write(
                    line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
                )
        data = output.getvalue().encode("utf-8")
        shortened = len(data) > limit
        return data[:limit].decode("utf-8", "ignore"), changed, shortened


class RunLock:
    """OS-Sperre gegen parallele CLI-/UI-Läufe, bei Prozessende automatisch gelöst.

    Windows sperrt ein Byte in der Lockdatei, Unix die Datei via flock. Ihre
    bloße Existenz reicht nicht: Eine normale Datei könnte nach Absturz verwaisen.
    """

    def __init__(self, home: Path):
        home.mkdir(parents=True, exist_ok=True)
        self.file = (home / "active.lock").open("a+b")
        self.file.write(b"0")
        self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            raise HarnessError("Ein anderer Harness-Lauf ist bereits aktiv") from exc

    def close(self) -> None:
        if self.file.closed:
            return
        if os.name == "nt":
            import msvcrt

            self.file.seek(0)
            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        self.file.close()
