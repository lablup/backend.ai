"""Tests for ``ExpandKernelGroupsRule``.

Verifies that per-replica kernel drafts are produced with the correct
cluster-layout assignments (``cluster_idx`` 1-based within role,
``cluster_hostname`` role+idx, ``local_rank`` 0-based global) and that
the group's ``execution_spec`` is propagated unchanged onto each
replica.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import ResourceSlotEntry
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    KernelResourceInput,
    SessionOptionsDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.expand_kernel_groups_rule import (
    ExpandKernelGroupsRule,
)


@pytest.fixture
def rule() -> ExpandKernelGroupsRule:
    return ExpandKernelGroupsRule()


@pytest.fixture
def context() -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
    )


def _make_execution_spec(image_id: ImageID, cpu: str = "1") -> KernelExecutionSpecDraft:
    return KernelExecutionSpecDraft(
        resource_input=KernelResourceInput(
            image_id=image_id,
            resources=(ResourceSlotEntry(resource_type="cpu", quantity=cpu),),
        ),
    )


def _make_group(
    role: str, replica_count: int, image_id: ImageID, cpu: str = "1"
) -> KernelGroupDraft:
    return KernelGroupDraft(
        role=role,
        replica_count=replica_count,
        execution_spec=_make_execution_spec(image_id, cpu),
    )


def _draft_with_groups(groups: tuple[KernelGroupDraft, ...]) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(options=SessionOptionsDraft(kernel_groups=groups))


class TestExpandKernelGroupsRule:
    async def test_noop_when_kernel_groups_unset(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """With no kernel_groups on the draft, kernel_specs stays empty."""
        draft = SessionResourceSpecDraft()
        result = await rule.prepare(draft, context)
        assert result.kernel_specs == ()

    async def test_single_group_single_replica(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """One group with replica_count=1 expands to a single draft."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((_make_group("main", 1, image_id),))

        result = await rule.prepare(draft, context)

        assert len(result.kernel_specs) == 1
        kernel = result.kernel_specs[0]
        assert kernel.cluster_role == "main"
        assert kernel.cluster_idx == 1
        assert kernel.cluster_hostname == "main1"
        assert kernel.local_rank == 0

    async def test_single_group_multi_replica_assigns_sequential_cluster_idx(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """A group with N replicas yields N drafts with cluster_idx 1..N."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((_make_group("worker", 3, image_id),))

        result = await rule.prepare(draft, context)

        assert len(result.kernel_specs) == 3
        assert [k.cluster_idx for k in result.kernel_specs] == [1, 2, 3]
        assert [k.cluster_hostname for k in result.kernel_specs] == [
            "worker1",
            "worker2",
            "worker3",
        ]
        assert [k.local_rank for k in result.kernel_specs] == [0, 1, 2]
        assert all(k.cluster_role == "worker" for k in result.kernel_specs)

    async def test_multi_group_flattens_in_declaration_order(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Multiple groups are flattened preserving the declared order."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((
            _make_group("main", 1, image_id),
            _make_group("sub", 2, image_id),
        ))

        result = await rule.prepare(draft, context)

        assert [k.cluster_role for k in result.kernel_specs] == [
            "main",
            "sub",
            "sub",
        ]
        assert [k.cluster_idx for k in result.kernel_specs] == [1, 1, 2]
        assert [k.cluster_hostname for k in result.kernel_specs] == [
            "main1",
            "sub1",
            "sub2",
        ]

    async def test_local_rank_is_global_across_groups(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """``local_rank`` is 0-based over the whole session, not per-role."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((
            _make_group("main", 2, image_id),
            _make_group("sub", 2, image_id),
        ))

        result = await rule.prepare(draft, context)

        assert [k.local_rank for k in result.kernel_specs] == [0, 1, 2, 3]

    async def test_execution_spec_copied_from_group(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Each replica carries the group's ``execution_spec`` fields."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((_make_group("worker", 2, image_id, cpu="4"),))

        result = await rule.prepare(draft, context)

        for kernel in result.kernel_specs:
            assert kernel.execution_spec.resource_input.image_id == image_id
            assert kernel.execution_spec.resource_input.resources == (
                ResourceSlotEntry(resource_type="cpu", quantity="4"),
            )

    async def test_empty_groups_tuple_produces_empty_kernel_specs(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecPreparationContext,
    ) -> None:
        """An explicit empty tuple yields no kernel drafts (distinct from None)."""
        draft = _draft_with_groups(())

        result = await rule.prepare(draft, context)

        assert result.kernel_specs == ()
