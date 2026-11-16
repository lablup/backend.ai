"""Tests for ``ExpandKernelGroupsRule``.

Verifies that per-replica kernel drafts are produced with the correct
cluster-layout assignments (``cluster_idx`` 1-based within role,
``cluster_hostname`` role+idx, ``local_rank`` 0-based global) and that
the group's ``execution_spec`` and ``preopen_ports`` are propagated
unchanged onto each replica, and each replica's ``vfolder_mounts``
comes from its own role's entry in the context.
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    MountPermission,
    ResourceSlotEntry,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
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
from ai.backend.manager.sokovan.scheduling_controller.preparers.resources.expand_kernel_groups_rule import (
    ExpandKernelGroupsRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


@pytest.fixture
def rule() -> ExpandKernelGroupsRule:
    return ExpandKernelGroupsRule()


def _make_mount(name: str) -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath(f"/mnt/host/{name}"),
        kernel_path=PurePosixPath(f"/home/work/{name}"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


def _context_with_mounts(
    vfolder_mounts_by_role: dict[str, tuple[VFolderMount, ...]],
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
            default_bootstrap_script=None,
            pending_session_count=0,
            pending_session_resource_slots={},
            vfolder_mounts_by_role=vfolder_mounts_by_role,
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


@pytest.fixture
def context() -> SessionSpecContext:
    return _context_with_mounts({})


def _make_execution_spec(image_id: ImageID, cpu: str = "1") -> KernelExecutionSpecDraft:
    return KernelExecutionSpecDraft(
        resource_input=KernelResourceInput(
            image_id=image_id,
            resources=(ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity=cpu),),
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


def _draft_with_groups(groups: tuple[KernelGroupDraft, ...]) -> ResourceSpecDraft:
    return ResourceSpecDraft(options=SessionOptionsDraft(kernel_groups=groups))


class TestExpandKernelGroupsRule:
    async def test_noop_when_kernel_groups_unset(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecContext,
    ) -> None:
        """With no kernel_groups on the draft, kernel_specs stays empty."""
        draft = ResourceSpecDraft()
        result = await rule.prepare(draft, context)
        assert result.kernel_specs == ()

    async def test_single_group_single_replica(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecContext,
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
        context: SessionSpecContext,
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
        context: SessionSpecContext,
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
        context: SessionSpecContext,
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
        context: SessionSpecContext,
    ) -> None:
        """Each replica carries the group's ``execution_spec`` fields."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((_make_group("worker", 2, image_id, cpu="4"),))

        result = await rule.prepare(draft, context)

        for kernel in result.kernel_specs:
            assert kernel.execution_spec.resource_input.image_id == image_id
            assert kernel.execution_spec.resource_input.resources == (
                ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="4"),
            )

    async def test_empty_groups_tuple_produces_empty_kernel_specs(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecContext,
    ) -> None:
        """An explicit empty tuple yields no kernel drafts (distinct from None)."""
        draft = _draft_with_groups(())

        result = await rule.prepare(draft, context)

        assert result.kernel_specs == ()

    async def test_preopen_ports_copied_per_group(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecContext,
    ) -> None:
        """Each replica carries its own group's preopen ports."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((
            KernelGroupDraft(
                role="main",
                replica_count=1,
                execution_spec=_make_execution_spec(image_id),
                preopen_ports=(8080,),
            ),
            KernelGroupDraft(
                role="worker",
                replica_count=2,
                execution_spec=_make_execution_spec(image_id),
                preopen_ports=(9090,),
            ),
        ))

        result = await rule.prepare(draft, context)

        assert [k.preopen_ports for k in result.kernel_specs] == [
            (8080,),
            (9090,),
            (9090,),
        ]

    async def test_vfolder_mounts_come_from_the_role_s_context_entry(
        self,
        rule: ExpandKernelGroupsRule,
    ) -> None:
        """Each replica mounts only the vfolders resolved for its own role."""
        image_id = ImageID(uuid.uuid4())
        main_mount = _make_mount("main-data")
        worker_mount = _make_mount("worker-data")
        draft = _draft_with_groups((
            _make_group("main", 1, image_id),
            _make_group("worker", 2, image_id),
        ))

        result = await rule.prepare(
            draft,
            _context_with_mounts({"main": (main_mount,), "worker": (worker_mount,)}),
        )

        assert [k.vfolder_mounts for k in result.kernel_specs] == [
            (main_mount,),
            (worker_mount,),
            (worker_mount,),
        ]

    async def test_role_absent_from_context_gets_no_mounts(
        self,
        rule: ExpandKernelGroupsRule,
        context: SessionSpecContext,
    ) -> None:
        """A resource-only caller resolved no mounts, so replicas carry none."""
        image_id = ImageID(uuid.uuid4())
        draft = _draft_with_groups((_make_group("main", 1, image_id),))

        result = await rule.prepare(draft, context)

        assert result.kernel_specs[0].vfolder_mounts == ()
