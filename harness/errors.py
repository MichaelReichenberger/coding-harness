"""Erwartete Fehlerarten; der Controller übersetzt sie in sichtbare Laufzustände."""


class HarnessError(Exception):
    """Basisklasse für verständliche Harness-Fehler."""


class ToolError(HarnessError):
    """Unerlaubte/ungültige Anfrage; als Beobachtung ans Modell zurückgeben."""


class SandboxError(HarnessError):
    """Ausführungsgrenze fehlt oder ist beschädigt; Lauf blockieren."""


class ModelError(HarnessError):
    """Transport- oder Antwortfehler; nur begrenzt wiederholen."""


class Cancelled(HarnessError):
    """Nutzerabbruch; keine weiteren Modellaktionen ausführen."""


class LimitReached(HarnessError):
    """Budget erschöpft; Diff und bisherigen Befund sichern."""
