import uuid

__all__ = ("ActionID",)


# One action run's identifier. Every audit row and reporter message a run emits
# carries it, which is what ties the rows of a fan-out back to the same run.
type ActionID = uuid.UUID
