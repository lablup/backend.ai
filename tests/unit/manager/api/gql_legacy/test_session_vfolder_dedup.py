"""Tests for ``_dedup_folder_ids`` feeding the session ``vfolder_nodes``."""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from ai.backend.common.types import (
    MountPermission,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.api.gql_legacy.session import _dedup_folder_ids


def _mount(
    name: str,
    *,
    folder_id: uuid.UUID | None = None,
    vfsubpath: str = ".",
) -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=folder_id or uuid.uuid4()),
        vfsubpath=PurePosixPath(vfsubpath),
        host_path=PurePosixPath(f"/mnt/host/{name}/{vfsubpath}"),
        kernel_path=PurePosixPath(f"/home/work/{name}"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


def test_collapses_same_folder_mounted_at_multiple_subpaths() -> None:
    # The reported bug: one vfolder mounted at several subpaths showed up as
    # several identical folder nodes. It must surface as a single folder id.
    folder_id = uuid.uuid4()
    mounts = [
        _mount("data", folder_id=folder_id, vfsubpath="."),
        _mount("data", folder_id=folder_id, vfsubpath="a"),
        _mount("data", folder_id=folder_id, vfsubpath="b"),
    ]

    assert _dedup_folder_ids(mounts) == [folder_id]


def test_keeps_distinct_folders() -> None:
    first, second = uuid.uuid4(), uuid.uuid4()
    mounts = [_mount("a", folder_id=first), _mount("b", folder_id=second)]

    assert _dedup_folder_ids(mounts) == [first, second]


def test_preserves_first_occurrence_order() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    mounts = [
        _mount("a", folder_id=a),
        _mount("b", folder_id=b),
        _mount("a", folder_id=a),
        _mount("c", folder_id=c),
    ]

    assert _dedup_folder_ids(mounts) == [a, b, c]


def test_empty() -> None:
    assert _dedup_folder_ids([]) == []
