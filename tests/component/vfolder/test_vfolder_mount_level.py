"""The REST v1 list answers the mount level of whoever reads it, not the folder default."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder import ListVFoldersQuery, ShareVFolderReq
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderMountPolicy
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


async def _listed_permission(
    registry: BackendAIClientRegistry,
    vfolder: VFolderFixtureData,
    query: ListVFoldersQuery | None = None,
) -> VFolderPermissionField:
    result = await registry.vfolder.list(query)
    [item] = [item for item in result.root if item.id == uuid.UUID(str(vfolder["id"])).hex]
    return item.permission


class TestVFolderListMountLevel:
    async def test_the_owner_reads_their_personal_folder_as_read_write(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        owner = regular_user_fixture.user_uuid
        personal = await vfolder_factory(
            user=str(owner),
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=owner)),
            default_mount_permission=VFolderMountPolicy.NONE,
        )

        permission = await _listed_permission(user_registry, personal)

        assert permission == VFolderPermissionField.READ_WRITE

    async def test_a_recipient_reads_the_level_they_were_shared(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        shared = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
            default_mount_permission=VFolderMountPolicy.READ_WRITE,
        )
        await admin_registry.vfolder.share(
            str(shared["id"]),
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )

        permission = await _listed_permission(user_registry, shared)

        assert permission == VFolderPermissionField.READ_ONLY

    async def test_a_reader_without_a_row_reads_the_folder_default(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        owner = regular_user_fixture.user_uuid
        personal = await vfolder_factory(
            user=str(owner),
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=owner)),
            default_mount_permission=VFolderMountPolicy.NONE,
        )

        permission = await _listed_permission(
            admin_registry,
            personal,
            ListVFoldersQuery(owner_user_email=regular_user_fixture.email),
        )

        assert permission == VFolderPermissionField.NONE
