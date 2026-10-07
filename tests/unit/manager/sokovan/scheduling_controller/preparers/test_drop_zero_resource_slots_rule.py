"""Tests for ``DropZeroResourceSlotsRule``."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    KernelResourceInput,
    ResourceSpecDraft,
    SessionOptionsDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.drop_zero_resource_slots_rule import (
    DropZeroResourceSlotsRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


@pytest.fixture
def rule() -> DropZeroResourceSlotsRule:
    return DropZeroResourceSlotsRule()


@pytest.fixture
def context() -> SessionSpecContext:
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
            pending_session_resource_slots={},
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _group(role: str, resources: dict[str, str], *, image_id: ImageID | None) -> KernelGroupDraft:
    return KernelGroupDraft(
        role=role,
        replica_count=1,
        execution_spec=KernelExecutionSpecDraft(
            resource_input=KernelResourceInput(
                image_id=image_id,
                resources=tuple(
                    ResourceSlotEntry(resource_type=ResourceSlotName(k), quantity=v)
                    for k, v in resources.items()
                ),
            ),
        ),
    )


def _slots(group: KernelGroupDraft) -> dict[str, str]:
    return {
        str(entry.resource_type): entry.quantity
        for entry in group.execution_spec.resource_input.resources
    }


class TestDropZeroResourceSlotsRule:
    async def test_drops_zero_slots_from_every_group(
        self,
        rule: DropZeroResourceSlotsRule,
        context: SessionSpecContext,
    ) -> None:
        """Groups with and without a resolved image both lose their zero slots."""
        draft = ResourceSpecDraft(
            options=SessionOptionsDraft(
                kernel_groups=(
                    _group(
                        "main",
                        {"cpu": "1", "mem": "1140850688", "cuda.device": "0", "cuda.shares": "0"},
                        image_id=ImageID(uuid.uuid4()),
                    ),
                    _group("sub", {"cpu": "2", "cuda.shares": "0.0"}, image_id=None),
                ),
            ),
        )

        result = await rule.prepare(draft, context)

        assert result.options.kernel_groups is not None
        main, sub = result.options.kernel_groups
        assert _slots(main) == {"cpu": "1", "mem": "1140850688"}
        assert _slots(sub) == {"cpu": "2"}

    async def test_keeps_non_zero_slots(
        self,
        rule: DropZeroResourceSlotsRule,
        context: SessionSpecContext,
    ) -> None:
        draft = ResourceSpecDraft(
            options=SessionOptionsDraft(
                kernel_groups=(
                    _group(
                        "main",
                        {"cpu": "1", "mem": "512m", "cuda.shares": "0.5"},
                        image_id=None,
                    ),
                ),
            ),
        )

        result = await rule.prepare(draft, context)

        assert result.options.kernel_groups is not None
        assert _slots(result.options.kernel_groups[0]) == {
            "cpu": "1",
            "mem": "512m",
            "cuda.shares": "0.5",
        }

    async def test_no_kernel_groups_is_noop(
        self,
        rule: DropZeroResourceSlotsRule,
        context: SessionSpecContext,
    ) -> None:
        draft = ResourceSpecDraft()

        result = await rule.prepare(draft, context)

        assert result is draft
