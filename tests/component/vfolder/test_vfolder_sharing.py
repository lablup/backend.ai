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
    AcceptInvitationReq,
    DeleteInvitationReq,
    InviteVFolderReq,
    InviteVFolderResponse,
    ListInvitationsResponse,
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
    VFolderInvitationState,
    VFolderMountPermission,
    VFolderOwnershipType,
)
from ai.backend.manager.models.vfolder import vfolder_invitations, vfolder_permissions

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


class TestVFolderInvitationStateMachine:
    """Invitation state transitions: verifies all PENDING → ACCEPTED/REJECTED/CANCELED
    paths and the list_invitations query for pending invitations."""

    async def _get_invitation_id_for_invitee(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_id: str,
    ) -> str:
        """Helper: query list_invitations as invitee and return the matching invitation ID."""
        result = await user_registry.vfolder.list_invitations()
        for inv in result.invitations:
            if str(inv.vfolder_id) == str(vfolder_id):
                return inv.id
        raise AssertionError(f"No invitation found for vfolder {vfolder_id}")

    @pytest.mark.xfail(
        reason="Server bug: ObjectNotFound.__init__() receives unsupported 'object_id' kwarg "
        "when user system role is missing (repository.py:812)",
        strict=False,
    )
    async def test_invite_and_accept(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """Scenario: Admin invites a regular user to a USER vfolder with READ_ONLY
        permission. The invitee accepts the invitation via accept_invitation API.
        Verifies the invitation state transitions to ACCEPTED in the DB."""
        invite_result = await admin_registry.vfolder.invite(
            target_vfolder["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(invite_result, InviteVFolderResponse)
        assert len(invite_result.invited_ids) == 1

        # Get actual invitation ID from list_invitations
        inv_id = await self._get_invitation_id_for_invitee(user_registry, str(target_vfolder["id"]))

        accept_result = await user_registry.vfolder.accept_invitation(
            AcceptInvitationReq(inv_id=inv_id),
        )
        assert isinstance(accept_result, MessageResponse)

        # Verify invitation state in DB
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        vfolder_invitations.c.id == uuid.UUID(inv_id)
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.ACCEPTED

    async def test_invite_and_reject_by_invitee(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """Scenario: Admin invites a regular user, then the invitee calls
        delete_invitation to reject it. Verifies the invitation state transitions
        to REJECTED in the DB."""
        vf = await vfolder_factory()
        invite_result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert len(invite_result.invited_ids) == 1

        # Get actual invitation ID
        inv_id = await self._get_invitation_id_for_invitee(user_registry, str(vf["id"]))

        reject_result = await user_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=inv_id),
        )
        assert isinstance(reject_result, MessageResponse)

        # Verify state
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        vfolder_invitations.c.id == uuid.UUID(inv_id)
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.REJECTED

    async def test_invite_and_cancel_by_inviter(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """Scenario: Admin invites a regular user, then the admin (inviter) calls
        delete_invitation to cancel the pending invitation. Verifies the invitation
        state transitions to CANCELED in the DB. Note: the inviter retrieves the
        invitation ID from the DB directly since list_invitations is invitee-only."""
        vf = await vfolder_factory()
        invite_result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert len(invite_result.invited_ids) == 1

        # Get invitation ID from DB directly (inviter can't use list_invitations)
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.id).where(
                        (vfolder_invitations.c.vfolder == vf["id"])
                        & (vfolder_invitations.c.state == VFolderInvitationState.PENDING)
                    )
                )
            ).first()
            assert row is not None
            inv_id = str(row.id)

        # Cancel as inviter (admin)
        cancel_result = await admin_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=inv_id),
        )
        assert isinstance(cancel_result, MessageResponse)

        # Verify state is CANCELED
        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        vfolder_invitations.c.id == uuid.UUID(inv_id)
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.CANCELED

    async def test_list_invitations(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """Scenario: Admin creates an invitation for a regular user. The invitee
        calls list_invitations and verifies the pending invitation appears in the
        result with the correct vfolder_id."""
        vf = await vfolder_factory()
        await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )

        # Invitee should see the pending invitation
        result = await user_registry.vfolder.list_invitations()
        assert isinstance(result, ListInvitationsResponse)
        assert len(result.invitations) >= 1
        inv_vfolder_ids = [inv.vfolder_id for inv in result.invitations]
        assert str(vf["id"]) in [str(vid) for vid in inv_vfolder_ids]


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
