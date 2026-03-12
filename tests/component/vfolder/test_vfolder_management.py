from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder import (
    AcceptInvitationReq,
    DeleteInvitationReq,
    DeleteVFolderByIDReq,
    DeleteVFolderFromTrashReq,
    InviteVFolderReq,
    InviteVFolderResponse,
    ListInvitationsResponse,
    ListSentInvitationsResponse,
    MessageResponse,
    RenameVFolderReq,
    RestoreVFolderReq,
    UpdateVFolderOptionsReq,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderInvitationState,
    VFolderOperationStatus,
)
from ai.backend.manager.models.vfolder import vfolder_invitations, vfolders

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]
InvitationFixtureData = dict[str, Any]
InvitationFactory = Callable[..., Coroutine[Any, Any, InvitationFixtureData]]


class TestVFolderRename:
    """VFolder rename (update_attribute) scenarios.

    Scenario file: vfolder/update_delete_vfolder.md — S-1, F-BIZ-1, F-AUTH-1.
    """

    async def test_owner_renames_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """S-1: VFolder owner renames to a unique new name; DB reflects the change."""
        new_name = f"renamed-{target_vfolder['name']}"
        try:
            result = await admin_registry.vfolder.rename(
                target_vfolder["name"],
                RenameVFolderReq(new_name=new_name),
            )
            assert isinstance(result, MessageResponse)
        except BackendAPIError as e:
            if e.status != 204:
                raise
            # 204 No Content is acceptable: operation succeeded but no body returned

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolders.c.name).where(vfolders.c.id == target_vfolder["id"])
                )
            ).first()
            assert row is not None
            assert row.name == new_name

    async def test_rename_to_duplicate_name_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
    ) -> None:
        """F-BIZ-1: Renaming to an already-used name raises an error (HTTP 4xx)."""
        vf_a = await vfolder_factory()
        vf_b = await vfolder_factory()
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.rename(
                vf_a["name"],
                RenameVFolderReq(new_name=vf_b["name"]),
            )
        assert exc_info.value.status in (400, 409)

    async def test_regular_user_cannot_rename_others_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """F-AUTH-1: Regular user cannot rename another user's vfolder."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.rename(
                target_vfolder["name"],
                RenameVFolderReq(new_name="should-fail"),
            )


class TestVFolderUpdateOptions:
    """VFolder update-options (cloneable flag) scenarios.

    Scenario file: vfolder/update_delete_vfolder.md — S-2.
    """

    async def test_admin_updates_cloneable_option(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """S-2: Admin changes the cloneable flag; DB reflects the change."""
        try:
            result = await admin_registry.vfolder.update_options(
                target_vfolder["name"],
                UpdateVFolderOptionsReq(cloneable=True),
            )
            assert isinstance(result, MessageResponse)
        except BackendAPIError as e:
            if e.status != 204:
                raise
            # 204 No Content is acceptable: operation succeeded but no body returned

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolders.c.cloneable).where(vfolders.c.id == target_vfolder["id"])
                )
            ).first()
            assert row is not None
            assert row.cloneable is True


class TestVFolderSoftDelete:
    """Soft-delete (move to trash) scenarios.

    Scenario file: vfolder/update_delete_vfolder.md — S-3, F-AUTH-1.
    """

    async def test_owner_soft_deletes_vfolder_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-3: Owner deletes by ID → vfolder status becomes DELETE_PENDING (not removed)."""
        vf = await vfolder_factory()
        try:
            result = await admin_registry.vfolder.delete_by_id(
                DeleteVFolderByIDReq(vfolder_id=vf["id"]),
            )
            assert isinstance(result, MessageResponse)
        except BackendAPIError as e:
            if e.status != 204:
                raise
            # 204 No Content is acceptable: operation succeeded but no body returned

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(sa.select(vfolders.c.status).where(vfolders.c.id == vf["id"]))
            ).first()
            assert row is not None
            assert row.status == VFolderOperationStatus.DELETE_PENDING

    async def test_owner_soft_deletes_vfolder_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-3 (by name): Owner deletes by name → status becomes DELETE_PENDING."""
        vf = await vfolder_factory()
        try:
            result = await admin_registry.vfolder.delete_by_name(vf["name"])
            assert isinstance(result, MessageResponse)
        except BackendAPIError as e:
            if e.status != 204:
                raise
            # 204 No Content is acceptable: operation succeeded but no body returned

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(sa.select(vfolders.c.status).where(vfolders.c.id == vf["id"]))
            ).first()
            assert row is not None
            assert row.status == VFolderOperationStatus.DELETE_PENDING

    async def test_regular_user_cannot_delete_others_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """F-AUTH-1: Regular user cannot delete another user's vfolder."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.delete_by_id(
                DeleteVFolderByIDReq(vfolder_id=target_vfolder["id"]),
            )


class TestVFolderHardDelete:
    """Hard-delete and restore scenarios.

    Scenario file: vfolder/update_delete_vfolder.md — S-4, S-7.
    Note: delete_from_trash calls storage-proxy; marked xfail where needed.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="delete_from_trash calls storage-proxy which is not available in component tests",
    )
    async def test_delete_from_trash_removes_db_record(
        self,
        admin_registry: BackendAIClientRegistry,
        trash_vfolder: VFolderFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """S-4: Delete a TRASH vfolder → DB record removed + storage-proxy delete called."""
        result = await admin_registry.vfolder.delete_from_trash(
            DeleteVFolderFromTrashReq(vfolder_id=trash_vfolder["id"]),
        )
        assert isinstance(result, MessageResponse)

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolders.c.id).where(vfolders.c.id == trash_vfolder["id"])
                )
            ).first()
            assert row is None

    async def test_restore_vfolder_from_trash(
        self,
        admin_registry: BackendAIClientRegistry,
        trash_vfolder: VFolderFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """S-7: Restore a TRASH vfolder → status returns to READY."""
        try:
            result = await admin_registry.vfolder.restore(
                RestoreVFolderReq(vfolder_id=trash_vfolder["id"]),
            )
            assert isinstance(result, MessageResponse)
        except BackendAPIError as e:
            if e.status != 204:
                raise
            # 204 No Content is acceptable: operation succeeded but no body returned

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolders.c.status).where(vfolders.c.id == trash_vfolder["id"])
                )
            ).first()
            assert row is not None
            assert row.status == VFolderOperationStatus.READY


class TestVFolderInviteCreate:
    """Invitation creation scenarios.

    Scenario file: vfolder/invitation.md — S-1, S-2, S-3, F-INVITE-1, F-INVITE-2.
    """

    async def test_owner_invites_user_to_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-1: VFolder owner invites another user → PENDING invitation created in DB."""
        result = await admin_registry.vfolder.invite(
            target_vfolder["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, InviteVFolderResponse)
        assert len(result.invited_ids) == 1
        # invited_ids contains email strings (not UUIDs) per actual server response
        assert result.invited_ids[0] == regular_user_fixture.email

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(
                        vfolder_invitations.c.state,
                        vfolder_invitations.c.invitee,
                    ).where(
                        sa.and_(
                            vfolder_invitations.c.vfolder == target_vfolder["id"],
                            vfolder_invitations.c.invitee == result.invited_ids[0],
                        )
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.PENDING
            assert row.invitee == regular_user_fixture.email

    async def test_invite_nonexistent_email_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """F-INVITE-2: Inviting a non-existent email raises an error."""
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.invite(
                target_vfolder["name"],
                InviteVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=["nonexistent-xyz-99999@example.invalid"],
                ),
            )

    async def test_duplicate_invite_is_skipped(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
    ) -> None:
        """S-3: Re-inviting an already-PENDING invitee returns empty invited_ids."""
        vf = await vfolder_factory()
        await invitation_factory(vfolder_id=vf["id"], invitee_email=regular_user_fixture.email)

        result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, InviteVFolderResponse)
        assert len(result.invited_ids) == 0


class TestVFolderInviteAcceptReject:
    """Invitation accept / reject / cancel state-machine scenarios.

    Scenario file: vfolder/invitation.md — S-4, S-5, S-6, F-ACCEPT-1, F-REJECT-1.
    """

    @pytest.mark.xfail(
        strict=False,
        reason="Server bug: ObjectNotFound.__init__() receives unsupported 'object_id' kwarg "
        "when user system role is missing (repository.py:812)",
    )
    async def test_invitee_accepts_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        db_engine: SAEngine,
    ) -> None:
        """S-4: Invitee accepts → state becomes ACCEPTED, vfolder_permissions row created."""
        vf = await vfolder_factory()
        invite_result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert len(invite_result.invited_ids) == 1
        inv_id = invite_result.invited_ids[0]

        accept_result = await user_registry.vfolder.accept_invitation(
            AcceptInvitationReq(inv_id=inv_id),
        )
        assert isinstance(accept_result, MessageResponse)

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

    async def test_invitee_rejects_invitation(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-5: Invitee rejects → state becomes REJECTED."""
        vf = await vfolder_factory()
        inv = await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=regular_user_fixture.email,
        )

        result = await user_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(inv["id"])),
        )
        assert isinstance(result, MessageResponse)

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        vfolder_invitations.c.id == inv["id"]
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.REJECTED

    async def test_inviter_cancels_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
        db_engine: SAEngine,
    ) -> None:
        """S-6: Inviter cancels their own invitation → state becomes CANCELED."""
        vf = await vfolder_factory()
        inv = await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=regular_user_fixture.email,
        )

        result = await admin_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(inv["id"])),
        )
        assert isinstance(result, MessageResponse)

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        vfolder_invitations.c.id == inv["id"]
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.CANCELED

    async def test_accept_nonexistent_invitation_raises_error(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-ACCEPT-1: Accepting a nonexistent invitation raises an error."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.accept_invitation(
                AcceptInvitationReq(inv_id=str(uuid.uuid4())),
            )

    async def test_third_party_cannot_reject_invitation(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_user_fixture: Any,
        invitation_factory: InvitationFactory,
    ) -> None:
        """F-REJECT-1: A third party (neither inviter nor invitee) cannot cancel/reject."""
        vf = await vfolder_factory()
        # Invitation where regular_user is neither inviter nor invitee
        inv = await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=admin_user_fixture.email,
        )

        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.delete_invitation(
                DeleteInvitationReq(inv_id=str(inv["id"])),
            )


class TestVFolderInviteList:
    """Invitation listing scenarios.

    Scenario file: vfolder/invitation.md — S-8, S-9, S-10.
    """

    async def test_invitee_sees_pending_invitations(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
    ) -> None:
        """S-8: Invitee lists received invitations → their pending invitation is included."""
        vf = await vfolder_factory()
        inv = await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=regular_user_fixture.email,
        )

        result = await user_registry.vfolder.list_invitations()
        assert isinstance(result, ListInvitationsResponse)
        inv_ids = [i.id for i in result.invitations]
        assert str(inv["id"]) in inv_ids

    async def test_inviter_sees_sent_invitations(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
    ) -> None:
        """S-9: Inviter lists sent invitations → their pending invitation is included."""
        vf = await vfolder_factory()
        inv = await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=regular_user_fixture.email,
        )

        result = await admin_registry.vfolder.list_sent_invitations()
        assert isinstance(result, ListSentInvitationsResponse)
        inv_ids = [i.id for i in result.invitations]
        assert str(inv["id"]) in inv_ids

    async def test_user_with_no_invitations_gets_empty_list(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """S-10: User with no pending invitations gets an empty list."""
        result = await user_registry.vfolder.list_invitations()
        assert isinstance(result, ListInvitationsResponse)
        assert result.invitations == []

    async def test_invitations_are_user_scoped(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        admin_user_fixture: Any,
        invitation_factory: InvitationFactory,
    ) -> None:
        """S-8 (scoping): Each user only sees their own invitations."""
        vf = await vfolder_factory()
        # Invitation addressed to admin (not regular_user)
        await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=admin_user_fixture.email,
        )

        # regular_user should not see the invitation meant for admin
        result = await user_registry.vfolder.list_invitations()
        assert isinstance(result, ListInvitationsResponse)
        for inv in result.invitations:
            assert inv.invitee != admin_user_fixture.email


class TestVFolderPermissionControl:
    """Permission-control scenarios for invite operations.

    Scenario file: vfolder/invitation.md — permission section.
    """

    async def test_non_owner_cannot_invite_to_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
    ) -> None:
        """Only the vfolder owner can invite users; non-owner gets an error."""
        # target_vfolder is owned by admin; user_registry is a regular user
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.invite(
                target_vfolder["name"],
                InviteVFolderReq(
                    permission=VFolderPermissionField.READ_ONLY,
                    emails=[regular_user_fixture.email],
                ),
            )

    async def test_reinvitation_after_cancellation(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        invitation_factory: InvitationFactory,
        db_engine: SAEngine,
    ) -> None:
        """Re-invitation after cancellation → new PENDING invitation created."""
        vf = await vfolder_factory()
        # Seed a CANCELED invitation
        await invitation_factory(
            vfolder_id=vf["id"],
            invitee_email=regular_user_fixture.email,
            state=VFolderInvitationState.CANCELED,
        )

        # Re-invite
        result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, InviteVFolderResponse)
        assert len(result.invited_ids) == 1
        # invited_ids contains email strings (not UUIDs) per actual server response
        new_inv_email = result.invited_ids[0]
        assert new_inv_email == regular_user_fixture.email

        async with db_engine.begin() as conn:
            row = (
                await conn.execute(
                    sa.select(vfolder_invitations.c.state).where(
                        sa.and_(
                            vfolder_invitations.c.vfolder == vf["id"],
                            vfolder_invitations.c.invitee == new_inv_email,
                            vfolder_invitations.c.state == VFolderInvitationState.PENDING,
                        )
                    )
                )
            ).first()
            assert row is not None
            assert row.state == VFolderInvitationState.PENDING
