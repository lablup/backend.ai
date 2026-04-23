"""Tests for ``ComputeKernelResourcesRule``.

Verifies the prepare-side of the legacy ``ResourceCalculator``:

  * intrinsic slots (``cpu`` / ``mem``) fall back to image minimums
    when the caller left them at zero / missing
  * explicit caller slot values win over image minimums
  * shmem resolution: draft override → image label → default
  * no-op on groups whose image is not in ``context.image_infos``
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    SessionOptionsDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions, ResourceOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import ImageInfo
from ai.backend.manager.sokovan.scheduling_controller.preparers.compute_kernel_resources_rule import (
    ComputeKernelResourcesRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
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
) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        image_infos=image_infos,
    )


def _draft(group: KernelGroupDraft) -> SessionSpecDraft:
    return SessionSpecDraft(options=SessionOptionsDraft(kernel_groups=(group,)))


class TestComputeKernelResourcesRule:
    async def test_fills_intrinsic_slots_from_image_min(
        self, rule: ComputeKernelResourcesRule
    ) -> None:
        """Zero/missing cpu and mem fall back to image minimums."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(image_id=image_id),
            ),
        )
        ctx = _context({image_id: _image(image_id, cpu_min="2", mem_min="512m")})
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        resources = result.options.kernel_groups[0].execution_spec.resources
        assert resources is not None
        assert resources["cpu"] == Decimal("2")
        assert resources["mem"] >= Decimal("512") * Decimal(1024 * 1024)

    async def test_preserves_caller_slot_values(self, rule: ComputeKernelResourcesRule) -> None:
        """Caller-set cpu / mem slots win over image minimums."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    image_id=image_id,
                    resources=ResourceSlot({"cpu": Decimal("8")}),
                ),
            ),
        )
        ctx = _context({image_id: _image(image_id, cpu_min="1")})
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        resources = result.options.kernel_groups[0].execution_spec.resources
        assert resources is not None
        assert resources["cpu"] == Decimal("8")

    async def test_shmem_defaults_from_image_label(self, rule: ComputeKernelResourcesRule) -> None:
        """Shmem resolves from ``ai.backend.resource.preferred.shmem`` image label."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(image_id=image_id),
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
        opts = result.options.kernel_groups[0].execution_spec.resource_opts
        assert opts is not None
        assert opts.shmem is not None
        # 2g == 2 * 1024 MiB
        assert opts.shmem == Decimal(2) * Decimal(1024 * 1024 * 1024)

    async def test_shmem_preserves_caller_value(self, rule: ComputeKernelResourcesRule) -> None:
        """Caller-set shmem survives the resolution pass."""
        image_id = ImageID(uuid.uuid4())
        caller_shmem = BinarySize.from_str("4g")
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(
                    image_id=image_id,
                    resource_opts=ResourceOpts(shmem=caller_shmem),
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
        opts = result.options.kernel_groups[0].execution_spec.resource_opts
        assert opts is not None
        assert opts.shmem == caller_shmem

    async def test_noop_when_image_info_missing(self, rule: ComputeKernelResourcesRule) -> None:
        """Groups whose image is not in the context are left unchanged."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft(
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=KernelExecutionSpecDraft(image_id=image_id),
            ),
        )
        ctx = _context({})  # no image infos supplied
        result = await rule.prepare(draft, ctx)

        assert result.options.kernel_groups is not None
        merged = result.options.kernel_groups[0].execution_spec
        assert merged.resources is None
        assert merged.resource_opts is None

    async def test_noop_when_kernel_groups_unset(self, rule: ComputeKernelResourcesRule) -> None:
        """With no ``kernel_groups``, the draft is returned unchanged."""
        draft = SessionSpecDraft()
        result = await rule.prepare(draft, _context({}))
        assert result is draft
