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
from ai.backend.manager.data.session.draft import KernelSpecDraft, SessionSpecDraft
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.resolve_vfolder_mounts_rule import (
    ResolveVFolderMountsRule,
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
) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        vfolder_mounts_by_role=vfolder_mounts_by_role or {},
    )


class TestResolveVFolderMountsRule:
    async def test_noop_when_context_empty(self) -> None:
        rule = ResolveVFolderMountsRule()
        draft = SessionSpecDraft(kernel_specs=(KernelSpecDraft(cluster_role="main"),))
        result = await rule.prepare(draft, _context())
        assert result is draft
        assert result.kernel_specs[0].vfolder_mounts == ()

    async def test_stamps_per_role_mounts_onto_matching_kernels(self) -> None:
        rule = ResolveVFolderMountsRule()
        mount = _mount("data")
        draft = SessionSpecDraft(
            kernel_specs=(
                KernelSpecDraft(cluster_role="main"),
                KernelSpecDraft(cluster_role="worker"),
            ),
        )
        result = await rule.prepare(draft, _context({"main": (mount,)}))
        assert result.kernel_specs[0].vfolder_mounts == (mount,)
        assert result.kernel_specs[1].vfolder_mounts == ()
