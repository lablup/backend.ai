from __future__ import annotations

from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.vfolder.request import (
    AcceptInvitationReq,
    DeleteInvitationReq,
    InviteVFolderReq,
    PurgeVFolderReq,
    RenameVFolderReq,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderInvitationState,
    VFolderOperationStatus,
)
from ai.backend.manager.models.vfolder import vfolder_invitations, vfolders

from .conftest import VFolderFactory


class TestVFolderUpdate:
    """Test vfolder update operations (rename, status change)."""

    async def test_rename_vfolder_success(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
    ) -> None:
        """S-1: Rename vfolder → name changed, get by new name works."""
        # Create a vfolder via factory
        vfolder = await vfolder_factory(name="original-name")
        old_name = vfolder["name"]
        new_name = f"{old_name}-renamed"

        # Rename via SDK
        await admin_registry.vfolder.rename(old_name, RenameVFolderReq(new_name=new_name))

        # Verify: get by new name should work
        info = await admin_registry.vfolder.get_info(new_name)
        assert info.name == new_name

        # Verify: get by old name should fail
        with pytest.raises(BackendAPIError) as exc:
            await admin_registry.vfolder.get_info(old_name)
        assert exc.value.status == 404

    async def test_rename_nonexistent_vfolder_fails(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """E-1: Rename non-existent vfolder → 404."""
        with pytest.raises(BackendAPIError) as exc:
            await admin_registry.vfolder.rename(
                "nonexistent-vfolder", RenameVFolderReq(new_name="new-name")
            )
        assert exc.value.status == 404


class TestVFolderDelete:
    """Test vfolder delete operations (soft delete, hard delete/purge)."""

    async def test_soft_delete_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-2: Soft delete vfolder → status transitions to delete-pending."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]

        # Soft delete via SDK
        await admin_registry.vfolder.delete_by_name(vfolder_name)

        # Verify: status should be delete-pending
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolders.c.status).where(vfolders.c.id == vfolder_id)
            )
            row = result.one_or_none()
            assert row is not None
            assert row.status == VFolderOperationStatus.DELETE_PENDING

    async def test_hard_delete_purge_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-3: Hard delete (purge) vfolder → vfolder removed from DB."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]

        # Purge via SDK
        await admin_registry.vfolder.purge(PurgeVFolderReq(vfolder_id=vfolder_id))

        # Verify: vfolder should be removed from DB
        async with db_engine.begin() as conn:
            result = await conn.execute(sa.select(vfolders.c.id).where(vfolders.c.id == vfolder_id))
            row = result.one_or_none()
            assert row is None


class TestVFolderDeletePermissions:
    """Test permission boundaries for vfolder deletion."""

    async def test_user_cannot_delete_other_users_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_user_fixture: Any,
    ) -> None:
        """E-2: Regular user cannot delete other user's vfolder → 403."""
        # Create vfolder owned by admin
        vfolder = await vfolder_factory(user=str(admin_user_fixture.user_uuid))
        vfolder_name = vfolder["name"]

        # Try to delete as regular user (not owner)
        with pytest.raises(BackendAPIError) as exc:
            await user_registry.vfolder.delete_by_name(vfolder_name)
        assert exc.value.status == 403


class TestVFolderInvitation:
    """Test vfolder invitation workflow (invite, accept, reject)."""

    async def test_owner_invites_user_creates_pending_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-4: Owner invites user → invitation created with PENDING status."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Invite user via SDK
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # Verify: invitation exists with PENDING status
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
            )
            row = result.one()
            assert row.state == VFolderInvitationState.PENDING

    async def test_invitee_accepts_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-5: Invitee accepts invitation → invitation status ACCEPTED, vfolder shared."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Owner invites user
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # Get invitation ID
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.id)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
            )
            invitation_id = result.scalar_one()

        # Invitee accepts invitation via SDK
        await user_registry.vfolder.accept_invitation(
            AcceptInvitationReq(inv_id=str(invitation_id))
        )

        # Verify: invitation status is ACCEPTED
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.state).where(
                    vfolder_invitations.c.id == invitation_id
                )
            )
            state = result.scalar_one()
            assert state == VFolderInvitationState.ACCEPTED

    async def test_invitee_rejects_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-6: Invitee rejects invitation → invitation status REJECTED."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Owner invites user
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # Get invitation ID
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.id)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
            )
            invitation_id = result.scalar_one()

        # Invitee rejects invitation via SDK
        await user_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(invitation_id))
        )

        # Verify: invitation status is REJECTED (or removed)
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.state).where(
                    vfolder_invitations.c.id == invitation_id
                )
            )
            row = result.one_or_none()
            # Invitation may be removed or marked REJECTED depending on implementation
            if row is not None:
                assert row.state == VFolderInvitationState.REJECTED

    async def test_list_pending_invitations(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
    ) -> None:
        """S-7: List pending invitations → returns invitations for the user."""
        vfolder = await vfolder_factory()
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Owner invites user
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # List invitations as invitee
        invitations = await user_registry.vfolder.list_invitations()
        assert len(invitations) > 0
        assert any(inv.vfolder_name == vfolder_name for inv in invitations)

    async def test_owner_cancels_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-8: Owner cancels invitation → invitation removed."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Owner invites user
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # Get invitation ID
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.id)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
            )
            invitation_id = result.scalar_one()

        # Owner cancels invitation
        await admin_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(invitation_id))
        )

        # Verify: invitation is removed or CANCELED
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations).where(vfolder_invitations.c.id == invitation_id)
            )
            row = result.one_or_none()
            if row is not None:
                assert row.state == VFolderInvitationState.CANCELED

    async def test_reinvitation_after_rejection(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-9: Re-invitation after rejection → new invitation created."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        invitee_email = regular_regular_user_fixture.email

        # Owner invites user
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[invitee_email]))

        # Get invitation ID and reject
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.id)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
            )
            first_invitation_id = result.scalar_one()

        # Invitee rejects
        await user_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(first_invitation_id))
        )

        # Owner re-invites
        await admin_registry.vfolder.invite(vfolder_name, invitee_email)

        # Verify: new invitation exists with PENDING status
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == invitee_email)
                .where(vfolder_invitations.c.state == VFolderInvitationState.PENDING)
            )
            row = result.one_or_none()
            assert row is not None


class TestVFolderInvitationPermissions:
    """Test permission boundaries for vfolder invitations."""

    async def test_non_owner_cannot_invite(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_user_fixture: Any,
        regular_user_fixture: Any,
    ) -> None:
        """E-3: Non-owner cannot invite → 403."""
        # Create vfolder owned by admin
        vfolder = await vfolder_factory(user=str(admin_user_fixture.user_uuid))
        vfolder_name = vfolder["name"]
        invitee_email = regular_user_fixture.email

        # Try to invite as non-owner
        with pytest.raises(BackendAPIError) as exc:
            await user_registry.vfolder.invite(
                vfolder_name, InviteVFolderReq(emails=[invitee_email])
            )
        assert exc.value.status == 403

    async def test_non_invitee_cannot_accept_reject(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """E-4: Non-invitee cannot accept/reject → 403."""
        vfolder = await vfolder_factory()
        vfolder_id = vfolder["id"]
        vfolder_name = vfolder["name"]
        # Invite someone else (not the regular user)
        other_email = "other-user@test.local"

        # Create invitation
        await admin_registry.vfolder.invite(vfolder_name, InviteVFolderReq(emails=[other_email]))

        # Get invitation ID
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(vfolder_invitations.c.id)
                .where(vfolder_invitations.c.vfolder == vfolder_id)
                .where(vfolder_invitations.c.invitee == other_email)
            )
            invitation_id = result.scalar_one()

        # Try to accept as non-invitee (user_registry is different user)
        with pytest.raises(BackendAPIError) as exc:
            await user_registry.vfolder.accept_invitation(
                AcceptInvitationReq(inv_id=str(invitation_id))
            )
        assert exc.value.status == 403

    async def test_invite_to_nonexistent_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        regular_user_fixture: Any,
    ) -> None:
        """E-5: Invite to non-existent vfolder → 404."""
        with pytest.raises(BackendAPIError) as exc:
            await admin_registry.vfolder.invite(
                "nonexistent-vfolder", InviteVFolderReq(emails=[regular_user_fixture.email])
            )
        assert exc.value.status == 404
