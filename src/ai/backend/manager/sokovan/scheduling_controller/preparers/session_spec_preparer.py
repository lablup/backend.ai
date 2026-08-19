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

from ai.backend.manager.data.session.draft import (
    ResourceSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.spec import SessionResourceSpec
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.draft_rule import (
    ResourceSpecDraftRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class SessionSpecPreparer:
    """Runs the ordered draft-rule chain and finalizes into a ``SessionSpec``.

    Rules come in two hierarchies: ``resource_rules``
    (:class:`ResourceSpecDraftRule`) determine the resource shape over
    the :class:`ResourceSpecDraft` slice, and ``spec_rules``
    (:class:`SessionSpecDraftRule`) complete the rest of the spec over
    the full draft (identity, network, container user, environ,
    internal data, mounts). :meth:`prepare` bridges the full draft
    through the resource slice then runs the spec rules; the fitting
    check runs only :meth:`prepare_resources`.

    Each rule receives the draft emitted by the previous one, so
    ordering matters (e.g. an image-resolution rule should run after
    the RG-default rule if the RG default image is a fallback for an
    unresolved request image). After the last rule runs, the draft is
    projected into the frozen spec.
    """

    _resource_rules: tuple[ResourceSpecDraftRule, ...]
    _spec_rules: tuple[SessionSpecDraftRule, ...]

    def __init__(
        self,
        resource_rules: Iterable[ResourceSpecDraftRule],
        spec_rules: Iterable[SessionSpecDraftRule],
    ) -> None:
        self._resource_rules = tuple(resource_rules)
        self._spec_rules = tuple(spec_rules)

    async def prepare(
        self,
        initial_draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpec:
        """Run the full chain and finalize.

        The full draft is bridged through the resource slice (resource
        rules see only options/kernel_specs), folded back, and then the
        spec rules complete the rest.
        """
        resource_draft = await self.prepare_resources(initial_draft.resource, context)
        draft = initial_draft.model_copy(update={"resource": resource_draft})
        for rule in self._spec_rules:
            draft = await rule.prepare(draft, context)
        return self._finalize(draft)

    async def prepare_resources(
        self,
        initial_draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        """Run only the resource-determination rules (no promotion)."""
        draft = initial_draft
        for rule in self._resource_rules:
            draft = await rule.prepare(draft, context)
        return draft

    def _finalize(self, draft: SessionResourceSpecDraft) -> SessionResourceSpec:
        """Project a fully-prepared draft into a frozen ``SessionResourceSpec``.

        The nested ``resource`` slice is flattened back into the flat
        spec shape here, so downstream consumers of the promoted spec
        are unaffected by the draft-side nesting.
        """
        payload = draft.model_dump(exclude_none=True)
        payload.update(payload.pop("resource", {}))
        return SessionResourceSpec.model_validate(payload)
