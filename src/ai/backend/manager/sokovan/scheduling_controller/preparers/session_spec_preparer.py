"""Runner for the draft-based preparer chain that produces a ``SessionSpec``.

Runs a sequence of :class:`SessionSpecDraftRule` in order and projects
the final draft into a frozen :class:`SessionSpec`. Projection is a
Pydantic round-trip: ``SessionSpecDraft.model_dump(exclude_none=True)``
feeds :meth:`SessionSpec.model_validate`, so the spec schema is the
single source of truth for both "what must be set" and error-path
reporting. Any field that should have been resolved but still sits at
``None`` is surfaced by ``BackendAIModel.model_validate`` as a
:class:`ModelValidationFailed` (HTTP 400) entry whose ``loc`` carries
the exact attribute path — no hand-maintained path strings.

The prior dict-based ``SessionPreparer`` (producing ``SessionEnqueueData``)
has been retired — this runner is the only path from caller input
through to the scheduler repository's writer transaction.
"""

from __future__ import annotations

from collections.abc import Iterable

from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
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
        initial_draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpec:
        """Run every rule in declaration order and finalize."""
        draft = initial_draft
        for rule in self._rules:
            draft = await rule.prepare(draft, context)
        return self._finalize(draft)

    def _finalize(self, draft: SessionSpecDraft) -> SessionSpec:
        """Project a fully-prepared draft into a frozen ``SessionSpec``.

        Draft fields left at ``None`` (never populated by a rule) drop
        out of the dump and surface as a :class:`ModelValidationFailed`
        (HTTP 400) raised by ``SessionSpec.model_validate`` itself,
        carrying the per-field ``loc`` paths.
        """
        return SessionSpec.model_validate(draft.model_dump(exclude_none=True))
