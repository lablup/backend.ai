"""Session validator that applies multiple validation rules."""

import logging
from collections.abc import Iterable

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationContext,
    SessionCreationSpec,
)

from .base import SessionValidatorRule

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionValidator:
    """
    Validator that applies multiple validation rules for session creation.
    """

    _rules: Iterable[SessionValidatorRule]

    def __init__(self, rules: Iterable[SessionValidatorRule]) -> None:
        self._rules = rules

    def validate(
        self,
        spec: SessionCreationSpec,
        context: SessionCreationContext,
    ) -> None:
        """
        Validate the session creation specification with all rules.

        Args:
            spec: Session creation specification
            context: Pre-fetched context with all required data (includes allowed_scaling_groups)

        Raises:
            InvalidAPIParameters or QuotaExceeded: If any validation fails
        """
        for rule in self._rules:
            log.debug(f"Applying validation rule: {rule.name()}")
            rule.validate(spec, context, context.allowed_scaling_groups)
