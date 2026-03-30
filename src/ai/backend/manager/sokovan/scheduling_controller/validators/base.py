"""Base classes for session validation and filtering rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
)


@dataclass
class ScalingGroupFilterRuleResult:
    """Result of a single scaling group filter rule."""

    allowed_groups: list[AllowedScalingGroup]
    """Scaling groups that passed this rule."""

    rejected_groups: dict[str, str]
    """Scaling groups that were rejected by this rule, mapped to rejection reason."""


@dataclass
class ScalingGroupFilterResult:
    """Final result of scaling group filtering with selected group."""

    allowed_groups: list[AllowedScalingGroup]
    """Scaling groups that passed all filters."""

    selected_scaling_group: str
    """The selected scaling group name (either specified or auto-selected)."""


class ScalingGroupFilterRule(ABC):
    """
    Abstract base class for scaling group filter rules.
    Each rule filters scaling groups based on specific criteria.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the filter rule name."""
        raise NotImplementedError

    @abstractmethod
    def filter(
        self,
        spec: SessionCreationSpec,
        allowed_groups: list[AllowedScalingGroup],
    ) -> ScalingGroupFilterRuleResult:
        """
        Filter scaling groups based on session creation specification.

        Args:
            spec: Session creation specification
            allowed_groups: List of scaling groups to filter

        Returns:
            ScalingGroupFilterRuleResult containing allowed and rejected groups with reasons
        """
        raise NotImplementedError


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
    ) -> None:
        """
        Validate a session creation specification.

        Args:
            spec: Session creation specification
            context: Pre-fetched context with all required data

        Raises:
            InvalidAPIParameters or QuotaExceeded: If validation fails
        """
        raise NotImplementedError
