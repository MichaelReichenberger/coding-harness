"""Vertrauenswürdiger Test-Einstieg, ausschließlich innerhalb des Containers.

Die unveränderten Upstream-Tests werden aus /trusted geladen. Der von ihnen
geprüfte Anwendungscode kommt aus /repo, also der bearbeiteten Laufkopie.
Baseline und Endprüfung verwenden exakt denselben Adapter.
"""

import ast
import sys
import unittest
from pathlib import Path

REPO = Path("/repo")
TRUSTED = Path("/trusted")


def main():
    if not Path("/.dockerenv").exists() or not REPO.is_dir():
        raise RuntimeError("Zielcode darf nur im Container ausgeführt werden")
    # Die geschützte Testkopie hat Vorrang vor dem tests-Paket des Zielrepositories.
    sys.path[:0] = [str(TRUSTED / "upstream"), str(REPO), str(TRUSTED)]
    check_id = sys.argv[1]
    if check_id == "lint":
        # S2-V: Standardbibliothek-Syntaxlint, kein Import oder Ausführen von Zielcode.
        errors = []
        for path in sorted(REPO.glob("*.py")):
            try:
                ast.parse(path.read_text("utf-8"), filename=path.name)
            except (SyntaxError, UnicodeError) as exc:
                errors.append(str(exc))
        print("\n".join(errors) if errors else "PASS syntax lint")
        return 1 if errors else 0
    if check_id == "feature":
        from feature import main as feature_main

        return feature_main()
    if check_id == "acceptance":
        from acceptance import main as acceptance_main

        return acceptance_main()
    modules = {
        "regression_core": "tests.test_supermarket",
        "regression_pricing": "pricing_regression",
    }
    suite = unittest.defaultTestLoader.loadTestsFromName(modules[check_id])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
