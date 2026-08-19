"""Per-kernel resource computation rule.

Absorbs the prepare-side of the legacy ``ResourceCalculator``:

  * Parses image min/max slots from :class:`ImageInfo.resource_spec`.
  * Resolves shared-memory size (draft override → image label default
    → ``DEFAULT_SHARED_MEMORY_SIZE``) and stores it on
    ``execution_spec.resource_opts.shmem``.
  * Fills intrinsic resource slots (``cpu`` / ``mem``) on the kernel
    group's ``execution_spec.resources`` from the image minimums when
    the caller left them at ``0`` / ``None``.

The legacy validate-side (image_min ≤ requested, shmem < mem) moves
to a dedicated validator rule (``ResourceLimitRule`` in the validator
chain) so this rule keeps a single responsibility — compute, don't
check.

No-op on groups whose image is not yet in ``context.global_info.image_infos``
(legacy also skipped those branches); the missing image is caught by
finalize / validator downstream.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import BinarySize, ResourceSlotEntry
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    ResourceSpecDraft,
)
from ai.backend.manager.data.session.options import ResourceOpts
from ai.backend.manager.defs import DEFAULT_SHARED_MEMORY_SIZE, INTRINSIC_SLOTS
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.draft_rule import (
    ResourceSpecDraftRule,
)
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import (
    image_min_slots,
    parse_quantity,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class ComputeKernelResourcesRule(ResourceSpecDraftRule):
    """Resolve intrinsic slots and shared-memory on each kernel group."""

    _SHMEM_IMAGE_LABEL = "ai.backend.resource.preferred.shmem"

    @override
    def name(self) -> str:
        return "compute_kernel_resources"

    @override
    async def prepare(
        self,
        draft: ResourceSpecDraft,
        context: SessionSpecContext,
    ) -> ResourceSpecDraft:
        if draft.options.kernel_groups is None:
            return draft

        new_groups = []
        for group in draft.options.kernel_groups:
            image_id = group.execution_spec.resource_input.image_id
            image_info = (
                context.global_info.image_infos.get(image_id) if image_id is not None else None
            )
            if image_info is None:
                new_groups.append(group)
                continue
            new_exec = self._resolve_execution_spec(group.execution_spec, image_info)
            new_groups.append(group.model_copy(update={"execution_spec": new_exec}))

        new_options = draft.options.model_copy(update={"kernel_groups": tuple(new_groups)})
        return draft.model_copy(update={"options": new_options})

    @classmethod
    def _resolve_execution_spec(
        cls,
        draft: KernelExecutionSpecDraft,
        image_info: ImageInfo,
    ) -> KernelExecutionSpecDraft:
        raw_min_slots = image_min_slots(image_info)
        resolved_opts = cls._resolve_resource_opts(
            draft.resource_input.resource_opts, image_info.labels
        )
        min_slots = cls._apply_shmem_to_mem_min(raw_min_slots, resolved_opts.shmem)
        resolved_resources = cls._fill_intrinsic_slots(draft.resource_input.resources, min_slots)
        return draft.model_copy(
            update={
                "resource_input": draft.resource_input.model_copy(
                    update={
                        "resources": resolved_resources,
                        "resource_opts": resolved_opts,
                    }
                ),
            }
        )

    @staticmethod
    def _apply_shmem_to_mem_min(
        min_slots: Mapping[str, Decimal],
        shmem: BinarySize | None,
    ) -> dict[str, Decimal]:
        """Inflate ``mem`` minimum by ``shmem``.

        Mirrors ``ResourceLimitRule._validate_kernel`` which adds shmem to
        ``min_slots["mem"]`` before comparing against the requested memory.
        Without this adjustment, defaults filled from the raw image minimum
        would be rejected by the validator.
        """
        adjusted: dict[str, Decimal] = dict(min_slots)
        if shmem is not None:
            adjusted["mem"] = adjusted.get("mem", Decimal(0)) + Decimal(int(shmem))
        return adjusted

    @classmethod
    def _resolve_resource_opts(
        cls,
        draft_opts: ResourceOpts | None,
        image_labels: Mapping[str, Any],
    ) -> ResourceOpts:
        if draft_opts is not None and draft_opts.shmem is not None:
            return draft_opts
        raw_shmem = image_labels.get(cls._SHMEM_IMAGE_LABEL) or DEFAULT_SHARED_MEMORY_SIZE
        try:
            shmem = BinarySize.finite_from_str(str(raw_shmem))
        except ValueError:
            shmem = BinarySize.finite_from_str(DEFAULT_SHARED_MEMORY_SIZE)
        if draft_opts is None:
            return ResourceOpts(shmem=shmem)
        return draft_opts.model_copy(update={"shmem": shmem})

    @staticmethod
    def _fill_intrinsic_slots(
        draft_resources: tuple[ResourceSlotEntry, ...],
        image_min_slots: Mapping[str, Decimal],
    ) -> tuple[ResourceSlotEntry, ...]:
        """Fill missing/zero intrinsic (``cpu``/``mem``) slots from image min."""
        existing = {entry.resource_type: entry for entry in draft_resources}
        result: list[ResourceSlotEntry] = list(draft_resources)
        for slot in INTRINSIC_SLOTS:
            slot_key = ResourceSlotName(str(slot))
            current = existing.get(slot_key)
            if current is None or parse_quantity(current.quantity) == Decimal(0):
                if slot_key in image_min_slots:
                    filled = ResourceSlotEntry(
                        resource_type=slot_key,
                        quantity=str(image_min_slots[slot_key]),
                    )
                    if current is None:
                        result.append(filled)
                    else:
                        result[result.index(current)] = filled
        return tuple(result)
