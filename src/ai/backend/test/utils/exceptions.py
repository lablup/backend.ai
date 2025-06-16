class UnexpectedSuccess(Exception):
    """Raised when a test marked as expected to fail actually succeeds."""

    def __init__(self, message="Test succeeded unexpectedly."):
        super().__init__(message)
