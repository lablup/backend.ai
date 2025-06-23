class DependencyNotSet(Exception):
    """Raised when a required dependency is not set."""

    def __init__(self, message="Required dependency is not set."):
        super().__init__(message)


class UnexpectedSuccess(Exception):
    """Raised when a test marked as expected to fail actually succeeds."""

    def __init__(self, message="Test succeeded unexpectedly."):
        super().__init__(message)
