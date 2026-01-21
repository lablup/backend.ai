"""Base classes for session preparation rules."""

from abc import ABC, abstractmethod
from typing import Any

from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)


class SessionPreparerRule(ABC):
    """
    Abstract base class for session preparer rules.
    Each rule implements specific preparation logic for session creation.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the preparer rule name."""
        raise NotImplementedError

    @abstractmethod
    def prepare(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        preparation_data: dict[str, Any],
    ) -> None:
        """
        Prepare/transform data for session creation.
        Updates the preparation_data dict in-place.

        Args:
            spec: Session creation specification
            context: Pre-fetched context with all required data
            preparation_data: Dictionary to store prepared data (modified in-place)
        """
        raise NotImplementedError
