"""Drop zero-quantity slots from every kernel group's requested resources.

Runs after :class:`.compute_kernel_resources_rule.ComputeKernelResourcesRule`
so zero ``cpu`` / ``mem`` are filled from image minimums before removal.
"""

from __future__ import annotations

from decimal import Decimal
from typing import override

from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.session.draft import (
    KernelGroupDraft,
    ResourceSpecDraft,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.draft_rule import (
    ResourceSpecDraftRule,
)
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class DropZeroResourceSlotsRule(ResourceSpecDraftRule):
    """Remove requested slots whose quantity is zero."""

    @override
    def name(self) -> str:
        return "drop_zero_resource_slots"

    @override
    async def prepare(
        self,
        draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        if draft.options.kernel_groups is None:
            return draft
        new_groups = tuple(self._drop_zero_slots(group) for group in draft.options.kernel_groups)
        new_options = draft.options.model_copy(update={"kernel_groups": new_groups})
        return draft.model_copy(update={"options": new_options})

    def _drop_zero_slots(self, group: KernelGroupDraft) -> KernelGroupDraft:
        resource_input = group.execution_spec.resource_input
        resources: tuple[ResourceSlotEntry, ...] = tuple(
            entry
            for entry in resource_input.resources
            if parse_quantity(entry.quantity) != Decimal(0)
        )
        if len(resources) == len(resource_input.resources):
            return group
        new_input = resource_input.model_copy(update={"resources": resources})
        new_exec = group.execution_spec.model_copy(update={"resource_input": new_input})
        return group.model_copy(update={"execution_spec": new_exec})
