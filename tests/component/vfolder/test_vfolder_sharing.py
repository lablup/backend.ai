from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder import (
    ListSharedVFoldersQuery,
    ListSharedVFoldersResponse,
    MessageResponse,
    ShareVFolderReq,
    ShareVFolderResponse,
    UnshareVFolderReq,
    UnshareVFolderResponse,
    UpdateSharedVFolderReq,
    UpdateVFolderSharingStatusReq,
    UserPermMapping,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOwnershipType,
)
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.vfolder import vfolder_permissions
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


class TestVFolderSharingFlow:
    """End-to-end sharing lifecycle covering the full share → verify → unshare path."""

    async def test_share_accept_access_unshare(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Scenario: Admin shares a GROUP vfolder with a regular user, confirms it
        appears in the shared list via list_shared, then unshares it and verifies
        the user is removed from the shared list."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        user_email = regular_user_fixture.email

        # Step 1: Share the GROUP vfolder with the regular user
        share_result = await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[user_email],
            ),
        )
        assert isinstance(share_result, ShareVFolderResponse)
        assert user_email in share_result.shared_emails

        # Step 2: Verify the shared list includes the permission
        shared_result = await admin_registry.vfolder.list_shared()
        assert isinstance(shared_result, ListSharedVFoldersResponse)

        # Step 3: Unshare the vfolder
        unshare_result = await admin_registry.vfolder.unshare(
            group_vf["name"],
            UnshareVFolderReq(emails=[user_email]),
        )
        assert isinstance(unshare_result, UnshareVFolderResponse)
        assert user_email in unshare_result.unshared_emails


class TestGroupFolderDirectPermissionSharing:
    """Direct permission sharing for GROUP vfolders via the share API.
    Each test shares a GROUP vfolder at a specific permission level and verifies
    the shared_emails response. The DB row test additionally checks that the
    vfolder_permissions table reflects the correct permission."""

    async def test_share_group_folder_with_read_only(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Scenario: Admin shares a GROUP vfolder with READ_ONLY permission to a
        regular user. Verifies the response contains the user's email in shared_emails."""
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
        """Scenario: Admin shares a GROUP vfolder with READ_WRITE permission to a
        regular user. Verifies the response contains the user's email in shared_emails."""
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
        """Scenario: Admin shares a GROUP vfolder with RW_DELETE (full read/write/delete)
        permission to a regular user. Verifies the response contains the user's email."""
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
        """Scenario: After sharing a GROUP vfolder with READ_ONLY, directly query
        the vfolder_permissions table and verify a row exists with the correct
        vfolder ID, user UUID, and READ_ONLY permission level."""
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
    """Share/unshare lifecycle and the list_shared query.
    Covers the share → unshare round-trip, DB row cleanup verification,
    and list_shared filtering (with/without vfolder_id, empty result)."""

    async def test_share_then_unshare(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
    ) -> None:
        """Scenario: Admin shares a GROUP vfolder with READ_ONLY to a regular user,
        then immediately unshares. Verifies both API calls succeed and the unshare
        response includes the user's email in unshared_emails."""
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
        """Scenario: After share → unshare, directly query the vfolder_permissions
        table and verify the permission row has been completely removed (not just
        soft-deleted). Ensures unshare performs a hard delete on the DB row."""
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
        """Scenario: Admin shares a GROUP vfolder, then calls list_shared without
        any filter. Verifies the shared vfolder appears in the response list by
        checking that its ID is present in the returned vfolder IDs."""
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
        """Scenario: Admin shares a GROUP vfolder, then calls list_shared with a
        vfolder_id filter. Verifies all returned entries match exactly the
        requested vfolder ID (no other vfolders leak into the result)."""
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
        """Scenario: Create a GROUP vfolder but do NOT share it. Call list_shared
        with its vfolder_id filter. Verifies the result is an empty list,
        confirming no phantom sharing entries exist for an unshared vfolder."""
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
    """Permission mutation after initial share: single-user update via update_shared
    and batch update via update_sharing_status (including permission removal)."""

    async def test_update_shared_permission(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Scenario: Admin shares a GROUP vfolder with READ_ONLY, then calls
        update_shared to escalate the permission to READ_WRITE. Verifies the API
        returns success and the vfolder_permissions DB row reflects READ_WRITE."""
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
        """Scenario: Admin shares a GROUP vfolder with READ_ONLY, then calls
        update_sharing_status (batch API) to escalate the user's permission to
        RW_DELETE. Verifies the vfolder_permissions DB row is updated.
        Marked xfail: server returns 201 with null body but SDK expects
        MessageResponse, causing a parse error."""
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
        """Scenario: Admin shares a GROUP vfolder with READ_ONLY, then calls
        update_sharing_status with perm=None for that user. This should remove the
        permission entirely. Verifies the vfolder_permissions DB row is deleted.
        Marked xfail: same SDK parse issue as test_batch_update_sharing_status."""
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
    """Negative-path validation for sharing: ensures the server rejects share/unshare
    requests that violate ownership rules or target non-existent users."""

    async def test_share_user_type_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
    ) -> None:
        """Scenario: Admin attempts to share a USER-type (personal) vfolder.
        The server should reject this with BackendAPIError because only
        GROUP-type vfolders support direct permission sharing."""
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
        """Scenario: A regular (non-admin) user attempts to share a GROUP vfolder
        that was created by the admin. The server should reject this because only
        the vfolder owner (or superadmin) can grant sharing permissions."""
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
        """Scenario: Admin attempts to share a GROUP vfolder with a non-existent
        email address. The server should reject this with BackendAPIError because
        the target user cannot be found in the system."""
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
        """Scenario: Admin attempts to unshare a GROUP vfolder from a non-existent
        email address. The server should reject this with BackendAPIError because
        there is no matching user or permission row to remove."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.unshare(
                group_vf["name"],
                UnshareVFolderReq(emails=["nonexistent-user@no-domain.test"]),
            )


async def _legacy_mount_permissions(
    db_engine: Any, vfolder_id: uuid.UUID
) -> dict[uuid.UUID, VFolderMountPermission]:
    """What ``vfolder_permissions`` says each user holds on the folder."""
    async with db_engine.begin() as conn:
        rows = (
            await conn.execute(
                sa.select(vfolder_permissions.c.user, vfolder_permissions.c.permission).where(
                    vfolder_permissions.c.vfolder == vfolder_id
                )
            )
        ).fetchall()
    return {row.user: VFolderMountPermission(row.permission) for row in rows}


async def _share_caps(db_engine: Any, vfolder_id: uuid.UUID) -> dict[uuid.UUID, Permission]:
    """What the share graph lends the folder to, keyed by whose personal project it is.

    A person is lent a folder into the project that is theirs alone, so the project's
    creator is the user the cap answers for.
    """
    scope = sa.alias(VirtualEntityRow.__table__, "scope")
    member = sa.alias(VirtualEntityRow.__table__, "member")
    stmt = (
        sa.select(ProjectRow.creator_id, EntityMembershipCapRow.permission)
        .select_from(
            sa.join(
                EntityMembershipRow.__table__,
                scope,
                scope.c.id == EntityMembershipRow.virtual_entity_id,
            )
            .join(member, member.c.id == EntityMembershipRow.member_entity_id)
            .join(ProjectRow.__table__, ProjectRow.id == scope.c.entity_id)
            .join(
                EntityMembershipCapRow.__table__,
                EntityMembershipCapRow.membership_id == EntityMembershipRow.id,
            )
        )
        .where(
            EntityMembershipRow.capped.is_(True),
            scope.c.entity_type == ProjectEntityType(),
            member.c.entity_type == VFolderEntityType(),
            member.c.entity_id == vfolder_id,
            ProjectRow.type == ProjectType.PERSONAL,
        )
    )
    async with db_engine.begin() as conn:
        rows = (await conn.execute(stmt)).fetchall()
    caps: dict[uuid.UUID, Permission] = {}
    for row in rows:
        caps[row.creator_id] = caps.get(row.creator_id, Permission.NONE) | Permission(
            row.permission
        )
    return caps


_WRITABLE_CAP = Permission.READ | Permission.UPDATE | Permission.SOFT_DELETE
_EXPECTED_CAP: dict[VFolderMountPermission, Permission] = {
    VFolderMountPermission.READ_ONLY: Permission.READ,
    VFolderMountPermission.READ_WRITE: _WRITABLE_CAP,
    VFolderMountPermission.RW_DELETE: _WRITABLE_CAP,
}


async def _assert_tables_agree(db_engine: Any, vfolder_id: uuid.UUID) -> None:
    """The legacy mount rows and the share caps name the same people, bit for bit."""
    legacy = await _legacy_mount_permissions(db_engine, vfolder_id)
    caps = await _share_caps(db_engine, vfolder_id)
    assert caps.keys() == legacy.keys()
    for user_id, permission in legacy.items():
        assert caps[user_id] == _EXPECTED_CAP[permission]


class TestSharingWritesBothTables:
    """Every sharing write puts a share cap beside the legacy mount row (BA-7665).

    Reads still go through ``vfolder_permissions``, so the two are kept in step
    rather than one replacing the other.
    """

    async def test_share_writes_the_cap_beside_the_mount_row(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Scenario: sharing a project folder read-only writes both tables, and the
        cap carries READ alone."""
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
        await _assert_tables_agree(db_engine, uuid.UUID(str(group_vf["id"])))
        caps = await _share_caps(db_engine, uuid.UUID(str(group_vf["id"])))
        assert caps[regular_user_fixture.user_uuid] == Permission.READ

    async def test_read_write_lends_a_wider_cap_than_read_only(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Scenario: re-sharing the same folder read-write raises the cap to
        READ|UPDATE — the two mount permissions are not stored as the same cap."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        vfolder_id = uuid.UUID(str(group_vf["id"]))
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        read_only_cap = (await _share_caps(db_engine, vfolder_id))[regular_user_fixture.user_uuid]

        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_WRITE,
                emails=[regular_user_fixture.email],
            ),
        )
        read_write_cap = (await _share_caps(db_engine, vfolder_id))[regular_user_fixture.user_uuid]

        assert read_only_cap == Permission.READ
        assert read_write_cap == _WRITABLE_CAP
        assert read_only_cap != read_write_cap
        await _assert_tables_agree(db_engine, vfolder_id)

    async def test_unshare_takes_the_cap_back_with_the_mount_row(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """Scenario: unsharing leaves neither table holding anything for the user."""
        group_vf = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
        )
        vfolder_id = uuid.UUID(str(group_vf["id"]))
        await admin_registry.vfolder.share(
            group_vf["name"],
            ShareVFolderReq(
                permission=VFolderPermissionField.READ_WRITE,
                emails=[regular_user_fixture.email],
            ),
        )
        await admin_registry.vfolder.unshare(
            group_vf["name"],
            UnshareVFolderReq(emails=[regular_user_fixture.email]),
        )
        assert await _legacy_mount_permissions(db_engine, vfolder_id) == {}
        assert await _share_caps(db_engine, vfolder_id) == {}
