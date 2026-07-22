"""Base interfaces for ``SessionSpec``-based validators.

The draft-based preparer chain feeds a finalized :class:`SessionSpec`
straight into validation without reshaping. Each rule implements
:class:`SessionSpecValidatorRule` and the runner
:class:`SessionSpecValidator` applies the declared rule sequence
against a :class:`SessionSpecContext` supplied by the
scheduling controller.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionSpecContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionSpecValidatorRule(ABC):
    """Abstract base class for SessionSpec-based validator rules."""

    @abstractmethod
    def name(self) -> str:
        """Return the validator rule name."""
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        """Validate a finalized ``SessionSpec`` against the shared context.

        Raises:
            BackendAIError subclass (``InvalidAPIParameters``,
            ``QuotaExceeded``, ...) when validation fails.
        """
        raise NotImplementedError


class SessionSpecValidator:
    """Applies an ordered chain of :class:`SessionSpecValidatorRule` rules."""

    _rules: tuple[SessionSpecValidatorRule, ...]

    def __init__(self, rules: Iterable[SessionSpecValidatorRule]) -> None:
        self._rules = tuple(rules)

    def validate(
        self,
        spec: SessionSpec,
        context: SessionSpecContext,
    ) -> None:
        for rule in self._rules:
            log.debug("Applying SessionSpec validation rule: {}", rule.name())
            rule.validate(spec, context)
