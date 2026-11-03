"""Repository-Navigation durch AST und Git-Diff; führt niemals Zielcode aus.

S2-N/C: Die gleiche Pfad-/Größenprüfung wie bei Dateiwerkzeugen gilt auch hier.
Eine Archivkopie besitzt absichtlich kein .git. Git vergleicht deshalb base/repo
mit --no-index; der ursprüngliche öffentliche Commit bleibt separat dokumentiert.
"""

import ast
import re

from harness.errors import ToolError
from harness.process import capture
from harness.sessions import checked_hashes


class Navigation:
    def __init__(self, tools, workspace):
        self.tools, self.workspace = tools, workspace

    def inspect(self, query=""):
        terms = set(re.findall(r"[a-z_][a-z_0-9]*", query.lower()))
        modules = []
        for path, relative in self.tools.files("."):
            if path.suffix != ".py":
                continue
            if len(modules) >= 80:
                break
            try:
                tree = ast.parse(self.tools.read(path))
                symbols, dependencies = [], []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append({"name": node.name, "line": node.lineno})
                    if isinstance(node, ast.Import):
                        dependencies.extend(alias.name for alias in node.names)
                    if isinstance(node, ast.ImportFrom):
                        dependencies.append(node.module or ".")
                names = {path.stem.lower()} | {s["name"].lower() for s in symbols}
                score = sum(any(term in name for name in names) for term in terms)
                modules.append(
                    {
                        "path": relative,
                        "symbols": symbols[:40],
                        "imports": sorted(set(dependencies))[:30],
                        "score": score,
                    }
                )
            except (SyntaxError, ValueError, RecursionError, ToolError) as exc:
                modules.append({"path": relative, "error": str(exc)[:200], "score": 0})
        modules.sort(key=lambda m: (-m["score"], m["path"]))
        selected = [m["path"] for m in modules if m["score"] > 0][:4]
        # Direkte lokale Abhängigkeiten ergänzen die Trefferauswahl.
        imports = {
            i.split(".")[0] for m in modules if m["path"] in selected for i in m.get("imports", [])
        }
        selected += [
            m["path"]
            for m in modules
            if m["path"] not in selected and m["path"].removesuffix(".py") in imports
        ]
        # Vor Git ebenfalls Links/Hardlinks ausschließen, auch nach externen Änderungen.
        checked_hashes(self.workspace.base)
        checked_hashes(self.workspace.repo)
        result = capture(
            [
                "git",
                "diff",
                "--no-index",
                "--no-ext-diff",
                "--no-textconv",
                "--name-status",
                str(self.workspace.base),
                str(self.workspace.repo),
            ],
            timeout=10,
            limit=8192,
        )
        if result.timed_out or result.exit_code not in (0, 1):
            raise ToolError("Git-Zustand nicht verfügbar: " + result.stderr[:200])
        # Nur relative Repositorypfade weitergeben, keine Hostpfade.
        git_text = result.stdout.replace(str(self.workspace.repo).replace("\\", "/") + "/", "")
        git_text = git_text.replace(str(self.workspace.base).replace("\\", "/") + "/", "")
        return {
            "selected_files": selected[:6],
            "git": {
                "starting_commit": self.workspace.target.commit,
                "comparison": "git diff --no-index base repo",
                "status": git_text,
                "truncated": result.truncated,
            },
            "modules": modules,
        }
