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
    """Runs the ordered draft-rule chain and finalizes into a ``SessionSpec``.

    Rules come in two groups: ``resource_rules`` determine the resource
    shape of the session (identity, RG defaults, kernel resources,
    group expansion) and ``spec_rules`` complete the rest of the spec
    (network, container user, environ, internal data, mounts). The full
    chain is their union in declaration order; the fitting check runs
    only the resource group via :meth:`prepare_resources`.

    Each rule receives the draft emitted by the previous one, so
    ordering matters (e.g. an image-resolution rule should run after
    the RG-default rule if the RG default image is a fallback for an
    unresolved request image). After the last rule runs, the draft is
    projected into the frozen spec.
    """

    _resource_rules: tuple[SessionSpecDraftRule, ...]
    _spec_rules: tuple[SessionSpecDraftRule, ...]

    def __init__(
        self,
        resource_rules: Iterable[SessionSpecDraftRule],
        spec_rules: Iterable[SessionSpecDraftRule],
    ) -> None:
        self._resource_rules = tuple(resource_rules)
        self._spec_rules = tuple(spec_rules)

    async def prepare(
        self,
        initial_draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpec:
        """Run the full chain (resource rules then spec rules) and finalize."""
        draft = await self._run(self._resource_rules, initial_draft, context)
        draft = await self._run(self._spec_rules, draft, context)
        return self._finalize(draft)

    async def prepare_resources(
        self,
        initial_draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpec:
        """Run only the resource-determination rules and finalize."""
        draft = await self._run(self._resource_rules, initial_draft, context)
        return self._finalize(draft)

    @staticmethod
    async def _run(
        rules: tuple[SessionSpecDraftRule, ...],
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        for rule in rules:
            draft = await rule.prepare(draft, context)
        return draft

    def _finalize(self, draft: SessionResourceSpecDraft) -> SessionResourceSpec:
        """Project a fully-prepared draft into a frozen ``SessionResourceSpec``."""
        return SessionResourceSpec.model_validate(draft.model_dump(exclude_none=True))
