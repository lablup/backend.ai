"""Tests for ``ComputeKernelResourcesRule``.

Verifies the prepare-side of the legacy ``ResourceCalculator``:

  * intrinsic slots (``cpu`` / ``mem``) fall back to image minimums
    when the caller left them at zero / missing
  * explicit caller slot values win over image minimums
  * shmem resolution: draft override → image label → default
  * no-op on groups whose image is not in ``context.global_info.image_infos``
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import BinarySize, ResourceSlotEntry
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo, ImageInfo
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    KernelResourceInput,
    ResourceSpecDraft,
    SessionOptionsDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions, ResourceOpts
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.compute_kernel_resources_rule import (
    ComputeKernelResourcesRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


@pytest.fixture
def rule() -> ComputeKernelResourcesRule:
    return ComputeKernelResourcesRule()


def _image(
    image_id: ImageID,
    *,
    cpu_min: str = "1",
    mem_min: str = "256m",
    labels: dict[str, Any] | None = None,
) -> ImageInfo:
    return ImageInfo(
        id=uuid.UUID(str(image_id)),
        canonical="repo.example.com/img:latest",
        architecture="x86_64",
        registry="repo.example.com",
        labels=labels or {},
        resource_spec={
            "cpu": {"min": cpu_min, "max": None},
            "mem": {"min": mem_min, "max": None},
        },
    )


def _context(
    image_infos: dict[ImageID, ImageInfo],
) -> SessionSpecContext:
    return SessionSpecContext(
        resource_group=ResourceGroupEnqueueInfo(
            defaults=DefaultSessionOptions(),
            network=None,
            allow_fractional=False,
            served_slot_names=frozenset(),
        ),
        user=UserEnqueueInfo(
            policy=None,
            container_user=ContainerUserInfo(),
            dotfiles=DotfileBundle(),
            pending_session_count=0,
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos=image_infos,
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft(group: KernelGroupDraft) -> ResourceSpecDraft:
    return ResourceSpecDraft(options=SessionOptionsDraft(kernel_groups=(group,)))


class TestComputeKernelResourcesRule:
    async def test_fills_intrinsic_slots_from_image_min(
        self, rule: ComputeKernelResourcesRule
    ) -> None:
        """Zero/missing cpu and mem fall back to image minimums (with shmem added to mem)."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(image_id=image_id),
                ),
            ),
        )
        ctx = _context({
            image_id: _image(
                image_id,
                cpu_min="2",
                mem_min="512m",
                labels={"ai.backend.resource.preferred.shmem": "64m"},
            )
        })
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        resources = result.options.kernel_groups[0].execution_spec.resource_input.resources
        resource_map = {entry.resource_type: Decimal(entry.quantity) for entry in resources}
        assert resource_map[ResourceSlotName("cpu")] == Decimal("2")
        # mem must include shmem so the result clears ResourceLimitRule's
        # `mem >= image_min_mem + shmem` check.
        expected_mem = Decimal(512 * 1024 * 1024) + Decimal(64 * 1024 * 1024)
        assert resource_map[ResourceSlotName("mem")] == expected_mem

    async def test_default_fill_passes_validator_minimum(
        self, rule: ComputeKernelResourcesRule
    ) -> None:
        """Default-filled mem must satisfy `image_min + shmem`."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(image_id=image_id),
                ),
            ),
        )
        ctx = _context({
            image_id: _image(
                image_id,
                mem_min="256m",
                labels={"ai.backend.resource.preferred.shmem": "64m"},
            )
        })
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        exec_spec = result.options.kernel_groups[0].execution_spec
        resource_map = {
            entry.resource_type: Decimal(entry.quantity)
            for entry in exec_spec.resource_input.resources
        }
        assert exec_spec.resource_input.resource_opts is not None
        shmem = exec_spec.resource_input.resource_opts.shmem
        assert shmem is not None
        image_min_mem = Decimal(256 * 1024 * 1024)
        assert resource_map[ResourceSlotName("mem")] >= image_min_mem + Decimal(int(shmem))

    async def test_preserves_caller_slot_values(self, rule: ComputeKernelResourcesRule) -> None:
        """Caller-set cpu / mem slots win over image minimums."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(
                        image_id=image_id,
                        resources=(
                            ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="8"),
                        ),
                    ),
                ),
            ),
        )
        ctx = _context({image_id: _image(image_id, cpu_min="1")})
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        resources = result.options.kernel_groups[0].execution_spec.resource_input.resources
        resource_map = {entry.resource_type: Decimal(entry.quantity) for entry in resources}
        assert resource_map[ResourceSlotName("cpu")] == Decimal("8")

    async def test_shmem_defaults_from_image_label(self, rule: ComputeKernelResourcesRule) -> None:
        """Shmem resolves from ``ai.backend.resource.preferred.shmem`` image label."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(image_id=image_id),
                ),
            ),
        )
        ctx = _context({
            image_id: _image(
                image_id,
                labels={"ai.backend.resource.preferred.shmem": "2g"},
            )
        })
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        opts = result.options.kernel_groups[0].execution_spec.resource_input.resource_opts
        assert opts is not None
        assert opts.shmem is not None
        # 2g == 2 * 1024 MiB
        assert opts.shmem == Decimal(2) * Decimal(1024 * 1024 * 1024)

    async def test_shmem_preserves_caller_value(self, rule: ComputeKernelResourcesRule) -> None:
        """Caller-set shmem survives the resolution pass."""
        image_id = ImageID(uuid.uuid4())
        caller_shmem = BinarySize(BinarySize.from_str("4g"))
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(
                        image_id=image_id,
                        resource_opts=ResourceOpts(shmem=caller_shmem),
                    ),
                ),
            ),
        )
        ctx = _context({
            image_id: _image(
                image_id,
                labels={"ai.backend.resource.preferred.shmem": "2g"},
            )
        })
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        opts = result.options.kernel_groups[0].execution_spec.resource_input.resource_opts
        assert opts is not None
        assert opts.shmem == caller_shmem

    async def test_noop_when_image_info_missing(self, rule: ComputeKernelResourcesRule) -> None:
        """Groups whose image is not in the context are left unchanged."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    resource_input=KernelResourceInput(image_id=image_id),
                ),
            ),
        )
        ctx = _context({})  # no image infos supplied
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        merged = result.options.kernel_groups[0].execution_spec
        assert merged.resource_input.resources == ()
        assert merged.resource_input.resource_opts is None

    async def test_noop_when_kernel_groups_unset(self, rule: ComputeKernelResourcesRule) -> None:
        """With no ``kernel_groups``, the draft is returned unchanged."""
        draft = ResourceSpecDraft()
        result = await rule.prepare(draft, _context({}))
        assert result is draft
