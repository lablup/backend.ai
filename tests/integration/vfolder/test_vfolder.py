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
    DeleteInvitationReq,
    DeleteVFolderByIDReq,
    GetVFolderIDReq,
    InviteVFolderReq,
    RenameVFolderReq,
    UpdateVFolderOptionsReq,
    VFolderGetInfoResponse,
    VFolderListResponse,
)
from ai.backend.manager.data.vfolder.types import VFolderInvitationState, VFolderMountPermission
from ai.backend.manager.models.vfolder import vfolder_invitations

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


@pytest.mark.integration
class TestVFolderLifecycle:
    async def test_vfolder_list_and_get_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
    ) -> None:
        """DB-seed -> list -> get_info -> get_id -> rename -> update_options -> delete -> verify deleted.

        Exercises the full vfolder data flow through the manager for DB-only operations.
        """
        vf = await vfolder_factory()
        original_name = vf["name"]

        # 1. List: seeded vfolder appears
        list_result = await admin_registry.vfolder.list()
        assert isinstance(list_result, VFolderListResponse)
        names = [item.name for item in list_result.items]
        assert original_name in names

        # 2. Get info by name
        info = await admin_registry.vfolder.get_info(original_name)
        assert isinstance(info, VFolderGetInfoResponse)
        assert info.item.name == original_name
        assert info.item.id == vf["id"].hex

        # 3. Get ID by name
        id_result = await admin_registry.vfolder.get_id(
            GetVFolderIDReq(name=original_name),
        )
        assert id_result.item.id == vf["id"].hex

        # 4. Rename
        new_name = f"renamed-{original_name}"
        await admin_registry.vfolder.rename(
            original_name,
            RenameVFolderReq(new_name=new_name),
        )
        renamed_info = await admin_registry.vfolder.get_info(new_name)
        assert renamed_info.item.name == new_name

        # 5. Update options
        await admin_registry.vfolder.update_options(
            new_name,
            UpdateVFolderOptionsReq(cloneable=True),
        )
        updated_info = await admin_registry.vfolder.get_info(new_name)
        assert updated_info.item.cloneable is True

        # 6. Delete (soft - moves to trash)
        await admin_registry.vfolder.delete_by_id(
            DeleteVFolderByIDReq(vfolder_id=vf["id"]),
        )

        # 7. Verify deleted: vfolder should no longer appear in normal list
        after_delete = await admin_registry.vfolder.list()
        after_names = [item.name for item in after_delete.items]
        assert new_name not in after_names

    async def test_vfolder_invitation_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """DB-seed -> invite -> list_invitations -> delete_invitation.

        Tests the invitation flow. Since accept_invitation requires the invitee
        to be the authenticated user, we use the user_registry for that step.
        """
        vf = await vfolder_factory()

        # 1. Invite the regular user
        result = await admin_registry.vfolder.invite(
            vf["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=["user-invite@test.local"],
            ),
        )
        assert isinstance(result.invited_ids, list)

        # 2. List sent invitations from admin perspective
        sent = await admin_registry.vfolder.list_sent_invitations()
        assert isinstance(sent.invitations, list)

        # 3. List invitations from admin perspective (admin may have none)
        invitations = await admin_registry.vfolder.list_invitations()
        assert isinstance(invitations.invitations, list)

        # 4. Seed a pending invitation directly for the admin user to delete
        inv_id = uuid.uuid4()
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(vfolder_invitations).values(
                    id=inv_id,
                    permission=VFolderMountPermission.READ_ONLY,
                    inviter="someone@test.local",
                    invitee="admin@test.local",
                    state=VFolderInvitationState.PENDING,
                    vfolder=vf["id"],
                )
            )

        # 5. Delete the invitation
        await admin_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(inv_id)),
        )


@pytest.mark.integration
class TestVFolderPermissionBoundary:
    async def test_regular_user_denied_admin_endpoints(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Systematic permission check: regular user cannot modify admin-owned vfolders."""
        # rename
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.rename(
                target_vfolder["name"],
                RenameVFolderReq(new_name="denied-rename"),
            )

        # update options
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.update_options(
                target_vfolder["name"],
                UpdateVFolderOptionsReq(cloneable=True),
            )

        # delete by id
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.delete_by_id(
                DeleteVFolderByIDReq(vfolder_id=target_vfolder["id"]),
            )

        # delete by name
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.delete_by_name(target_vfolder["name"])
