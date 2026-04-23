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
from ai.backend.manager.data.session.draft import SessionSpecDraft
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


def _context(*mounts: VFolderMount) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        vfolder_mounts=tuple(mounts),
    )


class TestResolveVFolderMountsRule:
    async def test_noop_when_context_empty(self) -> None:
        rule = ResolveVFolderMountsRule()
        draft = SessionSpecDraft()
        result = await rule.prepare(draft, _context())
        assert result.vfolder_mounts == ()

    async def test_copies_resolved_mounts_from_context(self) -> None:
        rule = ResolveVFolderMountsRule()
        draft = SessionSpecDraft()
        mount = _mount("data")
        result = await rule.prepare(draft, _context(mount))
        assert result.vfolder_mounts == (mount,)
