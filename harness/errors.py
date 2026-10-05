class HarnessError(Exception):
    """An expected, user-readable harness failure."""


class ToolError(HarnessError):
    pass


class SandboxError(HarnessError):
    pass


class ModelError(HarnessError):
    pass


class Cancelled(HarnessError):
    pass


class LimitReached(HarnessError):
    pass
