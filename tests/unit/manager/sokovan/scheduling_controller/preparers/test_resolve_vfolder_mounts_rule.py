"""Tests for ``ResolveVFolderMountsRule``."""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from ai.backend.common.types import (
    MountPermission,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    ResourceSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.resolve_vfolder_mounts_rule import (
    ResolveVFolderMountsRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


def _mount(name: str = "data") -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid.uuid4()),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath(f"/mnt/host/{name}"),
        kernel_path=PurePosixPath(f"/home/work/{name}"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


def _context(
    vfolder_mounts_by_role: dict[str, tuple[VFolderMount, ...]] | None = None,
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
            pending_session_resource_slots={},
            vfolder_mounts_by_role=vfolder_mounts_by_role or {},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft(*kernels: KernelSpecDraft) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(resource=ResourceSpecDraft(kernel_specs=kernels))


class TestResolveVFolderMountsRule:
    async def test_noop_when_context_empty(self) -> None:
        rule = ResolveVFolderMountsRule()
        draft = _draft(KernelSpecDraft(cluster_role="main"))
        result = await rule.prepare(draft, _context())
        assert result is draft
        assert result.resource.kernel_specs[0].vfolder_mounts == ()

    async def test_stamps_per_role_mounts_onto_matching_kernels(self) -> None:
        rule = ResolveVFolderMountsRule()
        mount = _mount("data")
        draft = _draft(
            KernelSpecDraft(cluster_role="main"),
            KernelSpecDraft(cluster_role="worker"),
        )
        result = await rule.prepare(draft, _context({"main": (mount,)}))
        assert result.resource.kernel_specs[0].vfolder_mounts == (mount,)
        assert result.resource.kernel_specs[1].vfolder_mounts == ()
