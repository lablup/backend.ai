"""Tests for ``DropZeroResourceSlotsRule``."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    SessionOptionsDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.drop_zero_resource_slots_rule import (
    DropZeroResourceSlotsRule,
)


@pytest.fixture
def rule() -> DropZeroResourceSlotsRule:
    return DropZeroResourceSlotsRule()


@pytest.fixture
def context() -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(resource_group_defaults=DefaultSessionOptions())


def _group(role: str, resources: dict[str, str], *, image_id: ImageID | None) -> KernelGroupDraft:
    return KernelGroupDraft(
        role=role,
        replica_count=1,
        execution_spec=KernelExecutionSpecDraft(
            image_id=image_id,
            resources=tuple(
                ResourceSlotEntry(resource_type=k, quantity=v) for k, v in resources.items()
            ),
        ),
    )


def _slots(group: KernelGroupDraft) -> dict[str, str]:
    return {entry.resource_type: entry.quantity for entry in group.execution_spec.resources}


class TestDropZeroResourceSlotsRule:
    async def test_drops_zero_slots_from_every_group(
        self,
        rule: DropZeroResourceSlotsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Groups with and without a resolved image both lose their zero slots."""
        draft = SessionSpecDraft(
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
        context: SessionSpecPreparationContext,
    ) -> None:
        draft = SessionSpecDraft(
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
        context: SessionSpecPreparationContext,
    ) -> None:
        draft = SessionSpecDraft()

        result = await rule.prepare(draft, context)

        assert result is draft
