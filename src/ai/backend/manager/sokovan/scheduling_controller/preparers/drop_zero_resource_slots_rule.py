"""Drop zero-quantity slots from every kernel group's requested resources.

Runs after :class:`.compute_kernel_resources_rule.ComputeKernelResourcesRule`
so zero ``cpu`` / ``mem`` are filled from image minimums before removal.
"""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.session.draft import (
    KernelGroupDraft,
    SessionSpecDraft,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity


class DropZeroResourceSlotsRule(SessionSpecDraftRule):
    """Remove requested slots whose quantity is zero."""

    def name(self) -> str:
        return "drop_zero_resource_slots"

    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        if draft.options.kernel_groups is None:
            return draft
        new_groups = tuple(self._drop_zero_slots(group) for group in draft.options.kernel_groups)
        new_options = draft.options.model_copy(update={"kernel_groups": new_groups})
        return draft.model_copy(update={"options": new_options})

    def _drop_zero_slots(self, group: KernelGroupDraft) -> KernelGroupDraft:
        execution_spec = group.execution_spec
        resources: tuple[ResourceSlotEntry, ...] = tuple(
            entry
            for entry in execution_spec.resources
            if parse_quantity(entry.quantity) != Decimal(0)
        )
        if len(resources) == len(execution_spec.resources):
            return group
        new_exec = execution_spec.model_copy(update={"resources": resources})
        return group.model_copy(update={"execution_spec": new_exec})
