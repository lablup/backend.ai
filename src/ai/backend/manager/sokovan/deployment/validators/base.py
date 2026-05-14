"""Base interfaces for deployment-revision validators.

Two entry points are provided because the v2 and legacy paths emit
different finalized shapes:

- :meth:`DeploymentRevisionValidator.validate` —
  v2 ``add_revision`` builds a :class:`DeploymentRevisionCreatorSpec` and
  validates it right before persistence.
- :meth:`DeploymentRevisionValidator.validate_legacy_revision_spec` —
  legacy paths (``build_creator_from_legacy_draft``,
  ``resolve_legacy_revision_spec``) project the merged draft into a
  :class:`ModelRevisionSpec` and validate it before returning.

Each rule implements both entry points so the same policy is enforced
regardless of which path the caller takes.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from ai.backend.common.types import SlotName
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.repositories.deployment.creators.revision import (
    DeploymentRevisionCreatorSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class DeploymentRevisionValidationContext:
    """Read-only global state the validator chain consumes."""

    required_slot_names: Iterable[SlotName] = field(default_factory=frozenset)


class DeploymentRevisionValidatorRule(ABC):
    """Abstract base class for deployment-revision validator rules."""

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        spec: DeploymentRevisionCreatorSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        """Validate the v2 :class:`DeploymentRevisionCreatorSpec`."""
        raise NotImplementedError

    @abstractmethod
    def validate_legacy_revision_spec(
        self,
        spec: ModelRevisionSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        """Validate the legacy :class:`ModelRevisionSpec`."""
        raise NotImplementedError


class DeploymentRevisionValidator:
    """Applies an ordered chain of :class:`DeploymentRevisionValidatorRule`."""

    _rules: Sequence[DeploymentRevisionValidatorRule]

    def __init__(self, rules: Iterable[DeploymentRevisionValidatorRule]) -> None:
        self._rules = tuple(rules)

    def validate(
        self,
        spec: DeploymentRevisionCreatorSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        for rule in self._rules:
            log.debug(f"Applying DeploymentRevisionCreatorSpec validation rule: {rule.name()}")
            rule.validate(spec, context)

    def validate_legacy_revision_spec(
        self,
        spec: ModelRevisionSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        for rule in self._rules:
            log.debug(f"Applying ModelRevisionSpec validation rule: {rule.name()}")
            rule.validate_legacy_revision_spec(spec, context)
