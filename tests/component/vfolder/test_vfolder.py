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
    InviteVFolderResponse,
    ListAllHostsResponse,
    ListAllowedTypesResponse,
    ListHostsResponse,
    ListInvitationsResponse,
    MessageResponse,
    RenameVFolderReq,
    UpdateVFolderOptionsReq,
    VFolderCreateReq,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderListResponse,
)
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.data.vfolder.types import VFolderInvitationState, VFolderMountPermission
from ai.backend.manager.models.vfolder import vfolder_invitations

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


class TestVFolderCreate:
    @pytest.mark.xfail(strict=True, reason="Requires live storage-proxy")
    async def test_create_requires_storage_proxy(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Attempt SDK create() to document the storage-proxy dependency."""
        await admin_registry.vfolder.create(
            VFolderCreateReq(name="test-create-proxy", folder_host="local"),
        )

    @pytest.mark.xfail(strict=True, reason="Requires live storage-proxy")
    async def test_regular_user_create_requires_storage_proxy(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user create attempt also requires storage-proxy."""
        await user_registry.vfolder.create(
            VFolderCreateReq(name="test-user-create-proxy", folder_host="local"),
        )


class TestVFolderList:
    async def test_admin_lists_vfolders(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Admin can list vfolders; the DB-seeded vfolder is visible."""
        result = await admin_registry.vfolder.list()
        assert isinstance(result, VFolderListResponse)
        names = [item.name for item in result.items]
        assert target_vfolder["name"] in names

    async def test_user_lists_own_vfolders(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """User can see vfolders owned by themselves."""
        user_uuid = regular_user_fixture.user_uuid
        vf = await vfolder_factory(
            user=str(user_uuid),
            creator="user-test@test.local",
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
        )
        result = await user_registry.vfolder.list()
        assert isinstance(result, VFolderListResponse)
        names = [item.name for item in result.items]
        assert vf["name"] in names


class TestVFolderGetInfo:
    @pytest.mark.xfail(
        strict=False,
        reason="get_info requires storage-proxy connection not available in component test",
    )
    async def test_admin_gets_vfolder_info(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Admin gets vfolder info by name."""
        result = await admin_registry.vfolder.get_info(target_vfolder["name"])
        assert isinstance(result, VFolderGetInfoResponse)
        assert result.item.name == target_vfolder["name"]
        assert result.item.id == target_vfolder["id"].hex

    async def test_get_nonexistent_vfolder_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """Querying a nonexistent vfolder name returns an error."""
        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.get_info("nonexistent-vfolder-xyz-12345")


class TestVFolderGetID:
    @pytest.mark.xfail(
        strict=False, reason="HMAC mismatch on GET with query params — SDK signing issue"
    )
    async def test_get_vfolder_id_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Retrieve vfolder ID from its name."""
        result = await admin_registry.vfolder.get_id(
            GetVFolderIDReq(name=target_vfolder["name"]),
        )
        assert isinstance(result, VFolderGetIDResponse)
        assert result.item.id == target_vfolder["id"].hex


class TestVFolderRename:
    @pytest.mark.xfail(
        strict=False,
        reason="get_info requires storage-proxy connection not available in component test",
    )
    async def test_admin_renames_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Admin renames a vfolder via SDK."""
        new_name = f"renamed-{target_vfolder['name']}"
        result = await admin_registry.vfolder.rename(
            target_vfolder["name"],
            RenameVFolderReq(new_name=new_name),
        )
        assert isinstance(result, MessageResponse)
        # Verify the rename took effect
        info = await admin_registry.vfolder.get_info(new_name)
        assert info.item.name == new_name

    async def test_regular_user_cannot_rename_others_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Regular user cannot rename a vfolder owned by another user."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.rename(
                target_vfolder["name"],
                RenameVFolderReq(new_name="should-fail"),
            )


class TestVFolderUpdateOptions:
    @pytest.mark.xfail(
        strict=False,
        reason=(
            "update-options handler reads permission column which may deserialize as NoneType"
            " when storage-proxy is not available"
        ),
    )
    async def test_admin_updates_vfolder_options(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Admin updates vfolder cloneable flag via SDK."""
        result = await admin_registry.vfolder.update_options(
            target_vfolder["name"],
            UpdateVFolderOptionsReq(cloneable=True),
        )
        assert isinstance(result, MessageResponse)
        # Verify the option was updated
        info = await admin_registry.vfolder.get_info(target_vfolder["name"])
        assert info.item.cloneable is True


class TestVFolderDelete:
    @pytest.mark.xfail(
        strict=False,
        reason="get_info requires storage-proxy connection not available in component test",
    )
    async def test_admin_deletes_vfolder_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
    ) -> None:
        """Admin soft-deletes a vfolder by ID (moves to trash)."""
        vf = await vfolder_factory()
        result = await admin_registry.vfolder.delete_by_id(
            DeleteVFolderByIDReq(vfolder_id=vf["id"]),
        )
        assert isinstance(result, MessageResponse)

    @pytest.mark.xfail(
        strict=False,
        reason="get_info requires storage-proxy connection not available in component test",
    )
    async def test_admin_deletes_vfolder_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
    ) -> None:
        """Admin soft-deletes a vfolder by name (moves to trash)."""
        vf = await vfolder_factory()
        result = await admin_registry.vfolder.delete_by_name(vf["name"])
        assert isinstance(result, MessageResponse)

    async def test_regular_user_cannot_delete_others_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Regular user cannot delete a vfolder owned by another user."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.delete_by_id(
                DeleteVFolderByIDReq(vfolder_id=target_vfolder["id"]),
            )


class TestVFolderHosts:
    async def test_list_hosts(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """List available vfolder hosts."""
        result = await admin_registry.vfolder.list_hosts()
        assert isinstance(result, ListHostsResponse)
        assert isinstance(result.allowed, list)

    async def test_list_all_hosts(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """Admin lists all available vfolder hosts."""
        result = await admin_registry.vfolder.list_all_hosts()
        assert isinstance(result, ListAllHostsResponse)
        assert isinstance(result.allowed, list)

    @pytest.mark.xfail(strict=False, reason="May require live storage-proxy for host discovery")
    async def test_list_allowed_types(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """List allowed vfolder types."""
        result = await admin_registry.vfolder.list_allowed_types()
        assert isinstance(result, ListAllowedTypesResponse)
        assert isinstance(result.allowed_types, list)


class TestVFolderInvitation:
    async def test_invite_user_to_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        regular_user_fixture: Any,
    ) -> None:
        """Invite a user to a vfolder via SDK."""
        result = await admin_registry.vfolder.invite(
            target_vfolder["name"],
            InviteVFolderReq(
                permission=VFolderPermissionField.READ_ONLY,
                emails=[regular_user_fixture.email],
            ),
        )
        assert isinstance(result, InviteVFolderResponse)
        assert isinstance(result.invited_ids, list)

    async def test_list_invitations(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """List received invitations (may be empty for admin)."""
        result = await admin_registry.vfolder.list_invitations()
        assert isinstance(result, ListInvitationsResponse)
        assert isinstance(result.invitations, list)

    @pytest.mark.xfail(
        strict=False,
        reason="delete_invitation returns 204 No Content, SDK expects MessageResponse",
    )
    async def test_delete_invitation(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        admin_user_fixture: Any,
        regular_user_fixture: Any,
        db_engine: Any,
    ) -> None:
        """Create and then delete an invitation."""
        # Seed an invitation directly in DB for deterministic testing
        inv_id = uuid.uuid4()
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(vfolder_invitations).values(
                    id=inv_id,
                    permission=VFolderMountPermission.READ_ONLY,
                    inviter=admin_user_fixture.email,
                    invitee=admin_user_fixture.email,
                    state=VFolderInvitationState.PENDING,
                    vfolder=target_vfolder["id"],
                )
            )
        result = await admin_registry.vfolder.delete_invitation(
            DeleteInvitationReq(inv_id=str(inv_id)),
        )
        assert isinstance(result, MessageResponse)
