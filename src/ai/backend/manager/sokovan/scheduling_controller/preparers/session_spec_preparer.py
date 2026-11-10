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

from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.manager.data.session.draft import (
    ResourceSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.spec import SessionResourceSpec
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.draft_rule import (
    ResourceSpecDraftRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.expand_kernel_groups_rule import (
    ExpandKernelGroupsRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.draft_rule import (
    SessionSpecDraftRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


@dataclass
class SessionSpecPreparerArgs:
    """Arguments for initializing SessionSpecPreparer.

    The four fields are the runner's four phases, in execution order.
    ``resource_rules`` and ``expand_rule`` operate on the
    :class:`ResourceSpecDraft` slice; ``pre_expand_spec_rules`` and
    ``spec_rules`` operate on the full :class:`SessionResourceSpecDraft`
    and are split by which side of ``expand_rule`` they run on.
    """

    resource_rules: Sequence[ResourceSpecDraftRule]
    pre_expand_spec_rules: Sequence[SessionSpecDraftRule]
    expand_rule: ExpandKernelGroupsRule
    spec_rules: Sequence[SessionSpecDraftRule]


class SessionSpecPreparer:
    """Runs the ordered draft-rule chain and finalizes into a ``SessionSpec``.

    Four phases run in order:

      1. ``resource_rules`` (:class:`ResourceSpecDraftRule`) determine
         the resource shape over the :class:`ResourceSpecDraft` slice.
      2. ``pre_expand_spec_rules`` (:class:`SessionSpecDraftRule`)
         complete each kernel group over the full draft — the values
         every replica of a group shares.
      3. ``expand_rule`` flattens the groups into per-replica kernel
         specs. This is the pivot the two ``SessionSpecDraftRule``
         phases are named after: the draft stops being group-shaped and
         becomes kernel-shaped.
      4. ``spec_rules`` (:class:`SessionSpecDraftRule`) complete the
         rest of the spec (identity, network, container user, internal
         data) now that the kernel specs exist.

    :meth:`prepare` runs all four; the fitting check runs
    :meth:`prepare_resources`, which is phases 1 and 3 only. The two
    ``SessionSpecDraftRule`` phases are skipped there because that
    caller holds only the resource slice, not the full draft they read
    (``internal_data_extras`` and the like), and the fitting decision
    needs neither.

    Each rule receives the draft emitted by the previous one, so
    ordering matters (e.g. an image-resolution rule should run after
    the RG-default rule if the RG default image is a fallback for an
    unresolved request image). After the last rule runs, the draft is
    projected into the frozen spec.
    """

    _resource_rules: tuple[ResourceSpecDraftRule, ...]
    _pre_expand_spec_rules: tuple[SessionSpecDraftRule, ...]
    _expand_rule: ExpandKernelGroupsRule
    _spec_rules: tuple[SessionSpecDraftRule, ...]

    def __init__(self, args: SessionSpecPreparerArgs) -> None:
        self._resource_rules = tuple(args.resource_rules)
        self._pre_expand_spec_rules = tuple(args.pre_expand_spec_rules)
        self._expand_rule = args.expand_rule
        self._spec_rules = tuple(args.spec_rules)

    async def prepare(
        self,
        initial_draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpec:
        """Run the full chain and finalize.

        The full draft is bridged through the resource slice (resource
        rules see only options/kernel_specs), folded back, the
        pre-expand spec rules complete the groups, expansion
        materializes the replicas, and then the spec rules complete the
        rest.
        """
        resource_draft = await self._run_resource_rules(initial_draft.resource, context)
        draft = self._apply_resource_draft(initial_draft, resource_draft)
        draft = await self._run_pre_expand_spec_rules(draft, context)
        expanded_resource = await self._expand_rule.prepare(draft.resource, context)
        draft = self._apply_resource_draft(draft, expanded_resource)
        draft = await self._run_spec_rules(draft, context)
        return self._finalize(draft)

    def _apply_resource_draft(
        self, session_draft: SessionResourceSpecDraft, resource_draft: ResourceSpecDraft
    ) -> SessionResourceSpecDraft:
        return session_draft.model_copy(update={"resource": resource_draft})

    async def prepare_resources(
        self,
        initial_draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        """Run only the resource-determination rules and expansion (no promotion)."""
        draft = await self._run_resource_rules(initial_draft, context)
        return await self._expand_rule.prepare(draft, context)

    async def _run_resource_rules(
        self,
        draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        for rule in self._resource_rules:
            draft = await rule.prepare(draft, context)
        return draft

    async def _run_pre_expand_spec_rules(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        for rule in self._pre_expand_spec_rules:
            draft = await rule.prepare(draft, context)
        return draft

    async def _run_spec_rules(
        self,
        draft: SessionResourceSpecDraft,
        context: SessionSpecContext,
    ) -> SessionResourceSpecDraft:
        for rule in self._spec_rules:
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
