"""Trusted adapter. Target imports and tests run only inside the Docker sandbox."""
import sys
import unittest
from pathlib import Path

REPO = Path("/repo")
TRUSTED = Path("/trusted")


def main():
    if not Path("/.dockerenv").exists() or not REPO.is_dir():
        raise RuntimeError("Zielcode darf nur im Container ausgeführt werden")
    # The tests package is the protected copy, never the repository's mutable tests.
    sys.path[:0] = [str(TRUSTED / "upstream"), str(REPO), str(TRUSTED)]
    check_id = sys.argv[1]
    if check_id == "acceptance":
        from acceptance import main as acceptance_main
        return acceptance_main()
    modules = {"regression_core": "tests.test_supermarket", "regression_pricing": "pricing_regression"}
    suite = unittest.defaultTestLoader.loadTestsFromName(modules[check_id])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
