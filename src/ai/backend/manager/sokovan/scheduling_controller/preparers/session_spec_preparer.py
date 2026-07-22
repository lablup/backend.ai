"""Runner for the draft-based preparer chain that produces a ``SessionSpec``.

Runs a sequence of :class:`SessionSpecDraftRule` in order and projects
the final draft into a frozen :class:`SessionSpec`. Projection is a
Pydantic round-trip: ``SessionSpecDraft.model_dump(exclude_none=True)``
feeds :meth:`SessionSpec.model_validate`, so the spec schema is the
single source of truth for both "what must be set" and error-path
reporting. Unresolved fields surface as :class:`IncompleteSessionSpec`
(raised by ``SessionSpec``'s ``build_validation_error`` override) with
the exact attribute path on ``extra_data["missing"]``.

The prior dict-based ``SessionPreparer`` (producing ``SessionEnqueueData``)
has been retired — this runner is the only path from caller input
through to the scheduler repository's writer transaction.
"""

from __future__ import annotations

from collections.abc import Iterable

from ai.backend.manager.data.session.draft import SessionResourceSpecDraft
from ai.backend.manager.data.session.spec import SessionResourceSpec
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class SessionSpecPreparer:
    """Runs an ordered chain of draft rules and finalizes into a ``SessionSpec``.

    Each rule receives the draft emitted by the previous one, so
    ordering matters (e.g. an image-resolution rule should run after
    the RG-default rule if the RG default image is a fallback for an
    unresolved request image). After the last rule runs, the draft is
    projected into the frozen spec.
    """

    _rules: tuple[SessionSpecDraftRule, ...]

    def __init__(self, rules: Iterable[SessionSpecDraftRule]) -> None:
        self._rules = tuple(rules)

    async def prepare(
        self,
        initial_draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpec:
        """Run every rule in declaration order and finalize."""
        draft = initial_draft
        for rule in self._rules:
            draft = await rule.prepare(draft, context)
        return self._finalize(draft)

    def _finalize(self, draft: SessionResourceSpecDraft) -> SessionResourceSpec:
        """Project a fully-prepared draft into a frozen ``SessionResourceSpec``."""
        return SessionResourceSpec.model_validate(draft.model_dump(exclude_none=True))
