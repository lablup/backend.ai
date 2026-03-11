from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder import (
    GetQuotaQuery,
    GetQuotaResponse,
    GetUsageQuery,
    GetUsageResponse,
    GetUsedBytesQuery,
    GetUsedBytesResponse,
    ListSharedVFoldersQuery,
    ListSharedVFoldersResponse,
    MessageResponse,
    ShareVFolderReq,
    ShareVFolderResponse,
    UnshareVFolderReq,
    UnshareVFolderResponse,
    UpdateQuotaReq,
    UpdateQuotaResponse,
    UpdateSharedVFolderReq,
    UpdateVFolderSharingStatusReq,
    UserPermMapping,
)
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.data.vfolder.types import VFolderMountPermission, VFolderOwnershipType
from ai.backend.manager.models.vfolder import vfolder_permissions

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


# ============================================================================
# Test Classes — VFolder Sharing
# ============================================================================


class TestGroupFolderDirectPermissionSharing:
    """Group folder direct permission sharing (vfolder_permissions table)."""

    async def test_share_group_folder_with_read_only(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Share a GROUP vfolder with READ_ONLY permission."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        result = await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, ShareVFolderResponse)
        assert regular_user_fixture.email in result.shared_emails

    async def test_share_group_folder_with_read_write(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Share a GROUP vfolder with READ_WRITE permission."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        result = await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_WRITE,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, ShareVFolderResponse)
        assert regular_user_fixture.email in result.shared_emails

    async def test_share_group_folder_with_write_delete(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Share a GROUP vfolder with WRITE_DELETE (full) permission."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        result = await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.RW_DELETE,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, ShareVFolderResponse)
        assert regular_user_fixture.email in result.shared_emails

    async def test_share_creates_permission_row_in_db(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Sharing creates a row in vfolder_permissions table."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_permissions).where(
                        (vfolder_permissions.c.vfolder == group_vf["id"])
                        & (vfolder_permissions.c.user == regular_user_fixture.user_uuid)
                    )
                )
            ).first()
            assert row is not None
            assert row.permission == VFolderMountPermission.READ_ONLY


class TestShareUnshareFlow:
    """Share and unshare lifecycle."""

    async def test_share_then_unshare(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Share then unshare should succeed."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        user_email = regular_user_fixture.email

        # Share
        share_result = await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[user_email],
            ),
        )
        assert user_email in share_result.shared_emails

        # Unshare
        unshare_result = await admin_registry.vfolder.unshare(
            group_vf["name"],
            UnshareVFolderReq(emails=[user_email]),
        )
        assert isinstance(unshare_result, UnshareVFolderResponse)
        assert user_email in unshare_result.unshared_emails

    async def test_unshare_removes_permission_row(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Unshare removes the permission row from DB."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        user_email = regular_user_fixture.email

        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[user_email],
            ),
        )
        await admin_registry.vfolder.unshare(
            group_vf["name"],
            UnshareVFolderReq(emails=[user_email]),
        )

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_permissions).where(
                        (vfolder_permissions.c.vfolder == group_vf["id"])
                        & (vfolder_permissions.c.user == regular_user_fixture.user_uuid)
                    )
                )
            ).first()
            assert row is None

    async def test_list_shared_after_sharing(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """list_shared returns shared vfolders."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        result = await admin_registry.vfolder.list_shared()
        assert isinstance(result, ListSharedVFoldersResponse)
        shared_vfolder_ids = [str(s.vfolder_id) for s in result.shared]
        assert str(group_vf["id"]) in shared_vfolder_ids

    async def test_list_shared_with_vfolder_id_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """list_shared with vfolder_id filter returns only that vfolder."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        result = await admin_registry.vfolder.list_shared(
            ListSharedVFoldersQuery(vfolder_id=group_vf["id"]),
        )
        assert isinstance(result, ListSharedVFoldersResponse)
        assert all(str(s.vfolder_id) == str(group_vf["id"]) for s in result.shared)

    async def test_list_shared_empty_when_no_sharing(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        group_fixture: uuid.UUID,
    ) -> None:
        """list_shared for a vfolder with no sharing returns empty."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        result = await admin_registry.vfolder.list_shared(
            ListSharedVFoldersQuery(vfolder_id=group_vf["id"]),
        )
        assert isinstance(result, ListSharedVFoldersResponse)
        assert len(result.shared) == 0


class TestSharePermissionUpdate:
    """Update sharing permissions after initial share."""

    async def test_update_shared_permission(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Update shared permission from READ_ONLY to READ_WRITE."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        result = await admin_registry.vfolder.update_shared(
            UpdateSharedVFolderReq(
                vfolder=group_vf["id"],
                user=regular_user_fixture.user_uuid,
                permission=VFolderPermissionField.READ_WRITE,
            ),
        )
        assert isinstance(result, MessageResponse)

        # Verify the permission was updated in DB
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_permissions.c.permission).where(
                        (vfolder_permissions.c.vfolder == group_vf["id"])
                        & (vfolder_permissions.c.user == regular_user_fixture.user_uuid)
                    )
                )
            ).first()
            assert row is not None
            assert row.permission == VFolderMountPermission.READ_WRITE

    @pytest.mark.xfail(
        strict=False,
        reason="Server returns 201 No Content but SDK expects MessageResponse body",
    )
    async def test_batch_update_sharing_status(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Batch update sharing permissions via update_sharing_status."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        result = await admin_registry.vfolder.update_sharing_status(
            UpdateVFolderSharingStatusReq(
                vfolder_id=group_vf["id"],
                user_perm_list=[
                    UserPermMapping(
                        user_id=regular_user_fixture.user_uuid,
                        perm=VFolderPermissionField.RW_DELETE,
                    ),
                ],
            ),
        )
        assert isinstance(result, MessageResponse)

        # Verify updated in DB
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_permissions.c.permission).where(
                        (vfolder_permissions.c.vfolder == group_vf["id"])
                        & (vfolder_permissions.c.user == regular_user_fixture.user_uuid)
                    )
                )
            ).first()
            assert row is not None
            assert row.permission == VFolderMountPermission.RW_DELETE

    @pytest.mark.xfail(
        strict=False,
        reason="Server returns 201 No Content but SDK expects MessageResponse body",
    )
    async def test_batch_remove_permission_via_null_perm(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Setting perm=None in batch update removes the permission."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        result = await admin_registry.vfolder.update_sharing_status(
            UpdateVFolderSharingStatusReq(
                vfolder_id=group_vf["id"],
                user_perm_list=[
                    UserPermMapping(
                        user_id=regular_user_fixture.user_uuid,
                        perm=None,
                    ),
                ],
            ),
        )
        assert isinstance(result, MessageResponse)

        # Verify permission row removed
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_permissions).where(
                        (vfolder_permissions.c.vfolder == group_vf["id"])
                        & (vfolder_permissions.c.user == regular_user_fixture.user_uuid)
                    )
                )
            ).first()
            assert row is None


class TestHostPermissionValidation:
    """Host permission validation — sharing requires appropriate role."""

    async def test_share_user_type_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
    ) -> None:
        """Sharing a USER-type vfolder should fail (only GROUP folders are sharable)."""
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.share(
                target_vfolder["name"],
                ShareVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=[regular_user_fixture.email],
                ),
            )

    async def test_regular_user_cannot_share_others_group_folder(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Regular user cannot share a GROUP vfolder they don't own."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.share(
                group_vf["name"],
                ShareVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=[admin_user_fixture.email],
                ),
            )

    async def test_share_with_nonexistent_email_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        group_fixture: uuid.UUID,
    ) -> None:
        """Sharing with a non-existent email returns an error."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.share(
                group_vf["name"],
                ShareVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=["nonexistent-user@no-domain.test"],
                ),
            )

    async def test_unshare_nonexistent_email_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        group_fixture: uuid.UUID,
    ) -> None:
        """Unsharing a non-existent email returns an error."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.unshare(
                group_vf["name"],
                UnshareVFolderReq(emails=["nonexistent-user@no-domain.test"]),
            )


# ============================================================================
# Test Classes — Storage Quota
# ============================================================================


class TestStorageQuotaScope:
    """Storage quota scope query and update (requires live storage-proxy)."""

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_get_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Query quota for an existing vfolder."""
        result = await admin_registry.vfolder.get_quota(
            GetQuotaQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetQuotaResponse)
        assert isinstance(result.data, dict)

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_update_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Update quota size for a vfolder."""
        result = await admin_registry.vfolder.update_quota(
            UpdateQuotaReq(
                folder_host="local",
                id=target_vfolder["id"],
                input={"size_bytes": 1024 * 1024 * 100},
            ),
        )
        assert isinstance(result, UpdateQuotaResponse)

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_get_usage(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Query usage statistics for a vfolder."""
        result = await admin_registry.vfolder.get_usage(
            GetUsageQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetUsageResponse)
        assert isinstance(result.data, dict)

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_get_used_bytes(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Query used bytes for a vfolder."""
        result = await admin_registry.vfolder.get_used_bytes(
            GetUsedBytesQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetUsedBytesResponse)
        assert isinstance(result.data, dict)

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_regular_user_can_get_own_quota(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """Regular user can query quota for their own vfolder."""
        user_uuid = regular_user_fixture.user_uuid
        vf = await vfolder_factory(
            user=str(user_uuid),
            creator="user-test@test.local",
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
        )
        result = await user_registry.vfolder.get_quota(
            GetQuotaQuery(folder_host="local", id=vf["id"]),
        )
        assert isinstance(result, GetQuotaResponse)

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_regular_user_cannot_update_others_quota(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Regular user cannot update quota for another user's vfolder."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.update_quota(
                UpdateQuotaReq(
                    folder_host="local",
                    id=target_vfolder["id"],
                    input={"size_bytes": 999999},
                ),
            )
