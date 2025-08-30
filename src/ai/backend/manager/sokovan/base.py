"""
Generic base handler for Sokovan operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from ai.backend.manager.defs import LockID

# Generic type for execution results
TResult = TypeVar("TResult")


class SokovanHandler(ABC, Generic[TResult]):
    """Generic base class for Sokovan operation handlers."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

    @abstractmethod
    async def execute(self) -> TResult:
        """Execute the operation.

        Returns:
            Result of the operation
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: TResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")
