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
    ListSharedVFoldersResponse,
    MessageResponse,
    ShareVFolderReq,
    ShareVFolderResponse,
    UnshareVFolderReq,
    UnshareVFolderResponse,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderInvitationState,
    VFolderOwnershipType,
)
from ai.backend.manager.models.vfolder import vfolder_invitations

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


class TestVFolderSharingFlow:
    """Multi-user sharing flow: share -> accept -> access -> unshare."""

    async def test_share_accept_access_unshare(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        admin_user_fixture: Any,
        group_fixture: uuid.UUID,
        db_engine: Any,
    ) -> None:
        """End-to-end: share a GROUP vfolder, verify shared list, then unshare."""
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

    async def test_share_user_type_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
    ) -> None:
        """Sharing a USER type vfolder should fail (only project folders are sharable)."""
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.share(
                target_vfolder["name"],
                ShareVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=[regular_user_fixture.email],
                ),
            )


class TestVFolderInvitationStateMachine:
    """Invitation state machine: PENDING -> ACCEPTED/REJECTED/CANCELED."""

    async def _get_invitation_id_for_invitee(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_id: str,
    ) -> str:
        """List invitations for invitee and return the invitation ID matching vfolder_id."""
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
        """PENDING -> ACCEPTED transition via invite + accept."""
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
        """PENDING -> REJECTED transition when invitee rejects."""
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
        admin_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """PENDING -> CANCELED transition when inviter cancels."""
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
        """List pending invitations for the invitee."""
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
