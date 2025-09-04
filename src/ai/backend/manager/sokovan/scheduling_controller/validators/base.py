"""Base classes for session validation rules."""

from abc import ABC, abstractmethod

from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)


class SessionValidatorRule(ABC):
    """
    Abstract base class for session validator rules.
    Each rule implements specific validation logic for session creation.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the validator rule name."""
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
        allowed_groups: list[AllowedScalingGroup],
    ) -> None:
        """
        Validate a session creation specification.

        Args:
            spec: Session creation specification
            context: Pre-fetched context with all required data
            allowed_groups: List of allowed scaling groups for the user

        Raises:
            InvalidAPIParameters or QuotaExceeded: If validation fails
        """
        raise NotImplementedError
