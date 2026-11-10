"""Tests for ``ResolveVFolderMountsRule``."""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import (
    MountInfoEntry,
    MountPermission,
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
    ResourceSpecDraft,
    SessionOptionsDraft,
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
            default_bootstrap_script=None,
            pending_session_count=0,
            pending_session_resource_slots={},
            vfolder_mounts_by_role=vfolder_mounts_by_role or {},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft(*groups: KernelGroupDraft) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(
        resource=ResourceSpecDraft(options=SessionOptionsDraft(kernel_groups=groups)),
    )


def _group(role: str, mounts: tuple[MountInfoEntry, ...] = ()) -> KernelGroupDraft:
    return KernelGroupDraft(
        role=role,
        replica_count=1,
        execution_spec=KernelExecutionSpecDraft(mounts=mounts),
    )


def _groups_by_role(draft: SessionResourceSpecDraft) -> dict[str, KernelGroupDraft]:
    groups = draft.resource.options.kernel_groups
    assert groups is not None
    return {group.role: group for group in groups}


class TestResolveVFolderMountsRule:
    async def test_noop_when_context_empty(self) -> None:
        """A resource-only caller resolved nothing, so requests stay as given."""
        rule = ResolveVFolderMountsRule()
        request = MountInfoEntry(vfolder_id=VFolderUUID(uuid.uuid4()))
        draft = _draft(_group("main", (request,)))
        result = await rule.prepare(draft, _context())
        assert result is draft
        assert _groups_by_role(result)["main"].execution_spec.mounts == (request,)

    async def test_noop_when_no_groups(self) -> None:
        rule = ResolveVFolderMountsRule()
        draft = _draft()
        result = await rule.prepare(draft, _context({"main": (_mount("data"),)}))
        assert result is draft

    async def test_request_entry_is_replaced_by_the_resolved_one(self) -> None:
        """The narrowed resolved entry carries concrete destination and permission."""
        rule = ResolveVFolderMountsRule()
        mount = _mount("data")
        request = MountInfoEntry(vfolder_id=VFolderUUID(mount.vfid.folder_id))
        draft = _draft(_group("main", (request,)))

        result = await rule.prepare(draft, _context({"main": (mount,)}))

        entries = _groups_by_role(result)["main"].execution_spec.mounts
        assert entries == (
            MountInfoEntry(
                vfolder_id=VFolderUUID(mount.vfid.folder_id),
                mount_destination="/home/work/data",
                mount_perm=MountPermission.READ_WRITE,
                subpath=".",
            ),
        )

    async def test_each_role_gets_its_own_mounts(self) -> None:
        rule = ResolveVFolderMountsRule()
        main_mount = _mount("main-data")
        worker_mount = _mount("worker-data")
        draft = _draft(_group("main"), _group("worker"))

        result = await rule.prepare(
            draft, _context({"main": (main_mount,), "worker": (worker_mount,)})
        )

        groups = _groups_by_role(result)
        assert [str(e.vfolder_id) for e in groups["main"].execution_spec.mounts] == [
            str(main_mount.vfid.folder_id)
        ]
        assert [str(e.vfolder_id) for e in groups["worker"].execution_spec.mounts] == [
            str(worker_mount.vfid.folder_id)
        ]

    async def test_auto_mounted_vfolder_is_added_to_the_group(self) -> None:
        """An entry the resolver injected on its own lands on the group too."""
        rule = ResolveVFolderMountsRule()
        auto_mount = _mount(".dotfiles")
        draft = _draft(_group("main"))

        result = await rule.prepare(draft, _context({"main": (auto_mount,)}))

        entries = _groups_by_role(result)["main"].execution_spec.mounts
        assert [e.mount_destination for e in entries] == ["/home/work/.dotfiles"]
