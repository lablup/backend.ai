"""
Tests for VFolderSharingService and VFolderInviteService functionality.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderInvitationData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import Forbidden
from ai.backend.manager.errors.storage import (
    VFolderAlreadyExists,
    VFolderGrantAlreadyExists,
    VFolderInvalidParameter,
    VFolderInvitationNotFound,
    VFolderNotFound,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import VFolderInvitationState
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    InviteVFolderAction,
    LeaveInvitedVFolderAction,
    ListInvitationAction,
    RejectInvitationAction,
    RevokeInvitedVFolderAction,
    UpdateInvitationAction,
    UpdateInvitedVFolderMountPermissionAction,
)
from ai.backend.manager.services.vfolder.actions.sharing import (
    ListSharedVFoldersAction,
    ShareVFolderAction,
    UnshareVFolderAction,
    UpdateVFolderSharingStatusAction,
)
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.services.sharing import VFolderSharingService


@pytest.fixture
def user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def vfolder_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_config_provider() -> MagicMock:
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(return_value=["user"])
    return provider


@pytest.fixture
def mock_vfolder_repo() -> MagicMock:
    return MagicMock(spec=VfolderRepository)


@pytest.fixture
def mock_user_repo() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def sharing_service(
    mock_config_provider: MagicMock,
    mock_vfolder_repo: MagicMock,
    mock_user_repo: MagicMock,
) -> VFolderSharingService:
    return VFolderSharingService(
        config_provider=mock_config_provider,
        vfolder_repository=mock_vfolder_repo,
        user_repository=mock_user_repo,
    )


@pytest.fixture
def invite_service(
    mock_config_provider: MagicMock,
    mock_vfolder_repo: MagicMock,
    mock_user_repo: MagicMock,
) -> VFolderInviteService:
    return VFolderInviteService(
        config_provider=mock_config_provider,
        vfolder_repository=mock_vfolder_repo,
        user_repository=mock_user_repo,
    )


def _make_user_data(
    user_uuid: uuid.UUID,
    *,
    domain_name: str | None = "default",
    email: str = "user@example.com",
    role: UserRole | None = UserRole.USER,
) -> MagicMock:
    user = MagicMock(spec=UserData)
    user.id = user_uuid
    user.uuid = user_uuid
    user.domain_name = domain_name
    user.email = email
    user.role = role
    return user


def _make_vfolder_data(
    vfolder_uuid: uuid.UUID,
    *,
    name: str = "test-vfolder",
    ownership_type: VFolderOwnershipType = VFolderOwnershipType.GROUP,
    group: uuid.UUID | None = None,
    host: str = "local:volume1",
) -> MagicMock:
    vf = MagicMock(spec=VFolderData)
    vf.id = vfolder_uuid
    vf.name = name
    vf.host = host
    vf.group = group or uuid.uuid4()
    vf.ownership_type = ownership_type
    vf.status = VFolderOperationStatus.READY
    return vf


# ============================================================
# ShareVFolderAction tests
# ============================================================


class TestShareVFolderAction:
    async def test_share_group_vfolder_to_multiple_users(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        emails = ["a@test.com", "b@test.com"]
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid)
        )
        mock_vfolder_repo.share_vfolder_with_users = AsyncMock(return_value=emails)

        action = ShareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            permission=VFolderMountPermission.READ_WRITE,
            emails=emails,
        )
        result = await sharing_service.share(action)

        assert result.shared_emails == emails
        mock_vfolder_repo.share_vfolder_with_users.assert_called_once()

    async def test_share_user_type_raises_error(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.USER)
        )

        action = ShareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            permission=VFolderMountPermission.READ_WRITE,
            emails=["a@test.com"],
        )

        with pytest.raises(VFolderNotFound, match="Only project folders are directly sharable"):
            await sharing_service.share(action)

    async def test_share_user_without_domain_raises_error(
        self,
        sharing_service: VFolderSharingService,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(
            return_value=_make_user_data(user_uuid, domain_name=None)
        )

        action = ShareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            permission=VFolderMountPermission.READ_WRITE,
            emails=["a@test.com"],
        )

        with pytest.raises(VFolderNotFound, match="User has no domain"):
            await sharing_service.share(action)

    async def test_share_nonexistent_vfolder_raises_error(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(return_value=None)

        action = ShareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            permission=VFolderMountPermission.READ_WRITE,
            emails=["a@test.com"],
        )

        with pytest.raises(VFolderNotFound):
            await sharing_service.share(action)


# ============================================================
# UnshareVFolderAction tests
# ============================================================


class TestUnshareVFolderAction:
    async def test_unshare_group_vfolder_removes_permissions(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        emails = ["a@test.com", "b@test.com"]
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid)
        )
        mock_vfolder_repo.unshare_vfolder_from_users = AsyncMock(return_value=emails)

        action = UnshareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            emails=emails,
        )
        result = await sharing_service.unshare(action)

        assert result.unshared_emails == emails

    async def test_unshare_user_type_raises_error(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.USER)
        )

        action = UnshareVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            resource_policy={},
            emails=["a@test.com"],
        )

        with pytest.raises(VFolderNotFound, match="Only project folders are directly unsharable"):
            await sharing_service.unshare(action)


# ============================================================
# ListSharedVFoldersAction tests
# ============================================================


class TestListSharedVFoldersAction:
    async def test_returns_sharing_permission_map(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        shared_user_uuid = uuid.uuid4()
        mock_vfolder_repo.list_shared_vfolder_permissions = AsyncMock(
            return_value=[
                {
                    "vfolder_id": vfolder_uuid,
                    "name": "shared-folder",
                    "status": VFolderOperationStatus.READY,
                    "group": uuid.uuid4(),
                    "vfolder_user": None,
                    "user": shared_user_uuid,
                    "email": "shared@test.com",
                    "permission": VFolderMountPermission.READ_ONLY,
                }
            ]
        )

        action = ListSharedVFoldersAction(vfolder_id=vfolder_uuid)
        result = await sharing_service.list_shared_vfolders(action)

        assert len(result.shared) == 1
        info = result.shared[0]
        assert info.vfolder_id == vfolder_uuid
        assert info.shared_user_email == "shared@test.com"
        assert info.permission == VFolderMountPermission.READ_ONLY
        assert info.folder_type == "project"

    async def test_filters_by_vfolder_id(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repo.list_shared_vfolder_permissions = AsyncMock(return_value=[])

        action = ListSharedVFoldersAction(vfolder_id=vfolder_uuid)
        await sharing_service.list_shared_vfolders(action)

        mock_vfolder_repo.list_shared_vfolder_permissions.assert_called_once_with(vfolder_uuid)

    async def test_no_permissions_returns_empty_list(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        mock_vfolder_repo.list_shared_vfolder_permissions = AsyncMock(return_value=[])

        action = ListSharedVFoldersAction(vfolder_id=None)
        result = await sharing_service.list_shared_vfolders(action)

        assert result.shared == []


# ============================================================
# UpdateVFolderSharingStatusAction tests
# ============================================================


class TestUpdateVFolderSharingStatusAction:
    async def test_update_permission(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        user_id = uuid.uuid4()
        mock_vfolder_repo.update_vfolder_sharing_status = AsyncMock()

        action = UpdateVFolderSharingStatusAction(
            vfolder_id=vfolder_uuid,
            to_update=[(user_id, VFolderMountPermission.READ_WRITE)],
            to_delete=[],
        )
        await sharing_service.update_sharing_status(action)

        mock_vfolder_repo.update_vfolder_sharing_status.assert_called_once_with(
            vfolder_uuid, [], [(user_id, VFolderMountPermission.READ_WRITE)]
        )

    async def test_delete_multiple_users(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_vfolder_repo.update_vfolder_sharing_status = AsyncMock()

        action = UpdateVFolderSharingStatusAction(
            vfolder_id=vfolder_uuid,
            to_update=[],
            to_delete=user_ids,
        )
        await sharing_service.update_sharing_status(action)

        mock_vfolder_repo.update_vfolder_sharing_status.assert_called_once_with(
            vfolder_uuid, user_ids, []
        )

    async def test_simultaneous_update_and_delete(
        self,
        sharing_service: VFolderSharingService,
        mock_vfolder_repo: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        update_user = uuid.uuid4()
        delete_user = uuid.uuid4()
        mock_vfolder_repo.update_vfolder_sharing_status = AsyncMock()

        action = UpdateVFolderSharingStatusAction(
            vfolder_id=vfolder_uuid,
            to_update=[(update_user, VFolderMountPermission.READ_WRITE)],
            to_delete=[delete_user],
        )
        await sharing_service.update_sharing_status(action)

        mock_vfolder_repo.update_vfolder_sharing_status.assert_called_once_with(
            vfolder_uuid,
            [delete_user],
            [(update_user, VFolderMountPermission.READ_WRITE)],
        )


# ============================================================
# InviteVFolderAction tests
# ============================================================


class TestInviteVFolderAction:
    async def test_invite_returns_pending_invitation_ids(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        invitation_id = str(uuid.uuid4())
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, name="my-folder")
        )
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.get_users_by_emails = AsyncMock(
            return_value=[(uuid.uuid4(), "invitee@test.com")]
        )
        mock_vfolder_repo.check_user_has_vfolder_permission = AsyncMock(return_value=False)
        mock_vfolder_repo.check_pending_invitation_exists = AsyncMock(return_value=False)
        mock_vfolder_repo.create_vfolder_invitation = AsyncMock(return_value=invitation_id)

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            mount_permission=VFolderMountPermission.READ_ONLY,
            invitee_emails=["invitee@test.com"],
        )
        result = await invite_service.invite(action)

        assert result.vfolder_uuid == vfolder_uuid
        assert invitation_id in result.invitation_ids

    async def test_invite_dot_prefix_raises_forbidden(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, name=".hidden-folder")
        )

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            mount_permission=VFolderMountPermission.READ_ONLY,
            invitee_emails=["invitee@test.com"],
        )

        with pytest.raises(Forbidden, match="dot-prefixed"):
            await invite_service.invite(action)

    async def test_invite_nonexistent_email_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid)
        )
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.get_users_by_emails = AsyncMock(return_value=[])

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            mount_permission=VFolderMountPermission.READ_ONLY,
            invitee_emails=["nobody@test.com"],
        )

        with pytest.raises(VFolderNotFound):
            await invite_service.invite(action)

    async def test_invite_existing_permission_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid)
        )
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.get_users_by_emails = AsyncMock(
            return_value=[(uuid.uuid4(), "invitee@test.com")]
        )
        mock_vfolder_repo.check_user_has_vfolder_permission = AsyncMock(return_value=True)

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            mount_permission=VFolderMountPermission.READ_ONLY,
            invitee_emails=["invitee@test.com"],
        )

        with pytest.raises(VFolderGrantAlreadyExists):
            await invite_service.invite(action)

    async def test_invite_duplicate_pending_skipped(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(user_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid)
        )
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.get_users_by_emails = AsyncMock(
            return_value=[(uuid.uuid4(), "invitee@test.com")]
        )
        mock_vfolder_repo.check_user_has_vfolder_permission = AsyncMock(return_value=False)
        mock_vfolder_repo.check_pending_invitation_exists = AsyncMock(return_value=True)

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            mount_permission=VFolderMountPermission.READ_ONLY,
            invitee_emails=["invitee@test.com"],
        )
        result = await invite_service.invite(action)

        assert result.invitation_ids == []
        mock_vfolder_repo.create_vfolder_invitation.assert_not_called()


# ============================================================
# AcceptInvitationAction tests
# ============================================================


class TestAcceptInvitationAction:
    async def test_accept_transitions_to_accepted(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_id = uuid.uuid4()
        invitee_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()

        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.vfolder = vfolder_uuid
        invitation_data.invitee = "invitee@test.com"
        invitation_data.permission = VFolderMountPermission.READ_ONLY.value

        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=invitation_data)
        mock_vfolder_repo.get_user_by_email = AsyncMock(
            return_value=(invitee_uuid, "invitee@test.com")
        )

        vfolder_data = _make_vfolder_data(vfolder_uuid, name="accepted-folder")
        mock_vfolder_repo.get_by_id = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repo.count_vfolder_with_name_for_user = AsyncMock(return_value=0)
        mock_vfolder_repo.create_vfolder_permission = AsyncMock()
        mock_vfolder_repo.update_invitation_state = AsyncMock()

        action = AcceptInvitationAction(invitation_id=invitation_id)
        result = await invite_service.accept_invitation(action)

        assert result.invitation_id == invitation_id
        mock_vfolder_repo.update_invitation_state.assert_called_once_with(
            invitation_id, VFolderInvitationState.ACCEPTED
        )
        mock_vfolder_repo.create_vfolder_permission.assert_called_once()

    async def test_accept_nonexistent_invitation_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=None)

        action = AcceptInvitationAction(invitation_id=uuid.uuid4())

        with pytest.raises(VFolderInvitationNotFound):
            await invite_service.accept_invitation(action)

    async def test_accept_duplicate_vfolder_name_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_id = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()
        invitee_uuid = uuid.uuid4()

        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.vfolder = vfolder_uuid
        invitation_data.invitee = "invitee@test.com"

        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=invitation_data)
        mock_vfolder_repo.get_user_by_email = AsyncMock(
            return_value=(invitee_uuid, "invitee@test.com")
        )
        mock_vfolder_repo.get_by_id = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, name="existing-name")
        )
        mock_vfolder_repo.count_vfolder_with_name_for_user = AsyncMock(return_value=1)

        action = AcceptInvitationAction(invitation_id=invitation_id)

        with pytest.raises(VFolderAlreadyExists):
            await invite_service.accept_invitation(action)


# ============================================================
# RejectInvitationAction tests
# ============================================================


class TestRejectInvitationAction:
    async def test_invitee_rejection_sets_rejected(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_id = uuid.uuid4()
        invitee_uuid = uuid.uuid4()

        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.inviter = "inviter@test.com"
        invitation_data.invitee = "invitee@test.com"

        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=invitation_data)
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="invitee@test.com")
        mock_vfolder_repo.update_invitation_state = AsyncMock()

        action = RejectInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=invitee_uuid,
        )
        result = await invite_service.reject_invitation(action)

        assert result.invitation_id == invitation_id
        mock_vfolder_repo.update_invitation_state.assert_called_once_with(
            invitation_id, VFolderInvitationState.REJECTED
        )

    async def test_inviter_rejection_sets_canceled(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_id = uuid.uuid4()
        inviter_uuid = uuid.uuid4()

        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.inviter = "inviter@test.com"
        invitation_data.invitee = "invitee@test.com"

        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=invitation_data)
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.update_invitation_state = AsyncMock()

        action = RejectInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=inviter_uuid,
        )
        result = await invite_service.reject_invitation(action)

        assert result.invitation_id == invitation_id
        mock_vfolder_repo.update_invitation_state.assert_called_once_with(
            invitation_id, VFolderInvitationState.CANCELED
        )

    async def test_third_party_rejection_raises_forbidden(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.inviter = "inviter@test.com"
        invitation_data.invitee = "invitee@test.com"

        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=invitation_data)
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="thirdparty@test.com")

        action = RejectInvitationAction(
            invitation_id=uuid.uuid4(),
            requester_user_uuid=uuid.uuid4(),
        )

        with pytest.raises(Forbidden):
            await invite_service.reject_invitation(action)

    async def test_reject_nonexistent_invitation_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        mock_vfolder_repo.get_invitation_by_id = AsyncMock(return_value=None)

        action = RejectInvitationAction(
            invitation_id=uuid.uuid4(),
            requester_user_uuid=uuid.uuid4(),
        )

        with pytest.raises(VFolderInvitationNotFound):
            await invite_service.reject_invitation(action)


# ============================================================
# UpdateInvitationAction tests
# ============================================================


class TestUpdateInvitationAction:
    async def test_update_permission_succeeds(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        invitation_id = uuid.uuid4()
        inviter_uuid = uuid.uuid4()

        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="inviter@test.com")
        mock_vfolder_repo.update_invitation_permission = AsyncMock()

        action = UpdateInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=inviter_uuid,
            mount_permission=VFolderMountPermission.READ_WRITE,
        )
        result = await invite_service.update_invitation(action)

        assert result.invitation_id == invitation_id
        mock_vfolder_repo.update_invitation_permission.assert_called_once_with(
            invitation_id, "inviter@test.com", VFolderMountPermission.READ_WRITE
        )

    async def test_update_by_nonexistent_user_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value=None)

        action = UpdateInvitationAction(
            invitation_id=uuid.uuid4(),
            requester_user_uuid=uuid.uuid4(),
            mount_permission=VFolderMountPermission.READ_WRITE,
        )

        with pytest.raises(VFolderNotFound):
            await invite_service.update_invitation(action)


# ============================================================
# ListInvitationAction tests
# ============================================================


class TestListInvitationAction:
    async def test_returns_pending_invitations(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        requester_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()
        invitation_id = uuid.uuid4()
        now = datetime.now(UTC)

        invitation_data = MagicMock(spec=VFolderInvitationData)
        invitation_data.id = invitation_id
        invitation_data.vfolder = vfolder_uuid
        invitation_data.invitee = "user@test.com"
        invitation_data.inviter = "inviter@test.com"
        invitation_data.permission = VFolderMountPermission.READ_ONLY
        invitation_data.created_at = now
        invitation_data.modified_at = None

        vfolder_data = _make_vfolder_data(vfolder_uuid, name="shared-folder")

        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="user@test.com")
        mock_vfolder_repo.get_pending_invitations_for_user = AsyncMock(
            return_value=[(invitation_data, vfolder_data)]
        )

        action = ListInvitationAction(requester_user_uuid=requester_uuid)
        result = await invite_service.list_invitation(action)

        assert len(result.info) == 1
        info = result.info[0]
        assert info.vfolder_id == vfolder_uuid
        assert info.vfolder_name == "shared-folder"
        assert info.inviter_user_email == "inviter@test.com"
        assert info.mount_permission == VFolderMountPermission.READ_ONLY
        assert info.status == VFolderInvitationState.PENDING

    async def test_no_invitations_returns_empty_list(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="user@test.com")
        mock_vfolder_repo.get_pending_invitations_for_user = AsyncMock(return_value=[])

        action = ListInvitationAction(requester_user_uuid=uuid.uuid4())
        result = await invite_service.list_invitation(action)

        assert result.info == []

    async def test_each_user_sees_only_own_invitations(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        requester_uuid = uuid.uuid4()
        mock_vfolder_repo.get_user_email_by_id = AsyncMock(return_value="user@test.com")
        mock_vfolder_repo.get_pending_invitations_for_user = AsyncMock(return_value=[])

        action = ListInvitationAction(requester_user_uuid=requester_uuid)
        await invite_service.list_invitation(action)

        mock_vfolder_repo.get_pending_invitations_for_user.assert_called_once_with("user@test.com")


# ============================================================
# LeaveInvitedVFolderAction tests
# ============================================================


class TestLeaveInvitedVFolderAction:
    async def test_leave_user_type_shared_vfolder(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        requester_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()

        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(requester_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.USER)
        )
        mock_vfolder_repo.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repo.delete_vfolder_permission = AsyncMock()

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_uuid,
            requester_user_uuid=requester_uuid,
        )
        result = await invite_service.leave_invited_vfolder(action)

        assert result.vfolder_uuid == vfolder_uuid
        mock_vfolder_repo.delete_vfolder_permission.assert_called_once_with(
            vfolder_uuid, requester_uuid
        )

    async def test_leave_group_type_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        requester_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()

        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(requester_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.GROUP)
        )

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_uuid,
            requester_user_uuid=requester_uuid,
        )

        with pytest.raises(VFolderInvalidParameter, match="Cannot leave a group vfolder"):
            await invite_service.leave_invited_vfolder(action)

    async def test_superadmin_can_delete_via_shared_user_uuid(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        admin_uuid = uuid.uuid4()
        shared_user_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()

        mock_user_repo.get_user_by_uuid = AsyncMock(
            return_value=_make_user_data(admin_uuid, role=UserRole.SUPERADMIN)
        )
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.USER)
        )
        mock_vfolder_repo.get_user_info = AsyncMock(return_value=(UserRole.SUPERADMIN, "default"))
        mock_vfolder_repo.delete_vfolder_permission = AsyncMock()

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_uuid,
            requester_user_uuid=admin_uuid,
            shared_user_uuid=shared_user_uuid,
        )
        result = await invite_service.leave_invited_vfolder(action)

        assert result.vfolder_uuid == vfolder_uuid
        mock_vfolder_repo.delete_vfolder_permission.assert_called_once_with(
            vfolder_uuid, shared_user_uuid
        )

    async def test_non_superadmin_specifying_other_user_raises_error(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
        mock_user_repo: MagicMock,
    ) -> None:
        requester_uuid = uuid.uuid4()
        other_uuid = uuid.uuid4()
        vfolder_uuid = uuid.uuid4()

        mock_user_repo.get_user_by_uuid = AsyncMock(return_value=_make_user_data(requester_uuid))
        mock_vfolder_repo.get_by_id_validated = AsyncMock(
            return_value=_make_vfolder_data(vfolder_uuid, ownership_type=VFolderOwnershipType.USER)
        )
        mock_vfolder_repo.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_uuid,
            requester_user_uuid=requester_uuid,
            shared_user_uuid=other_uuid,
        )

        with pytest.raises(InsufficientPrivilege):
            await invite_service.leave_invited_vfolder(action)


# ============================================================
# RevokeInvitedVFolderAction tests
# ============================================================


class TestRevokeInvitedVFolderAction:
    async def test_revoke_deletes_permission(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        vfolder_uuid = uuid.uuid4()
        shared_user_uuid = uuid.uuid4()

        mock_vfolder_repo.delete_vfolder_permission = AsyncMock()

        action = RevokeInvitedVFolderAction(
            vfolder_id=vfolder_uuid,
            shared_user_id=shared_user_uuid,
        )
        result = await invite_service.revoke_invited_vfolder(action)

        assert result.vfolder_id == vfolder_uuid
        assert result.shared_user_id == shared_user_uuid
        mock_vfolder_repo.delete_vfolder_permission.assert_called_once_with(
            vfolder_uuid, shared_user_uuid
        )


# ============================================================
# UpdateInvitedVFolderMountPermissionAction tests
# ============================================================


class TestUpdateInvitedVFolderMountPermissionAction:
    async def test_update_mount_permission(
        self,
        invite_service: VFolderInviteService,
        mock_vfolder_repo: MagicMock,
    ) -> None:
        vfolder_uuid = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_vfolder_repo.update_invited_vfolder_mount_permission = AsyncMock()

        action = UpdateInvitedVFolderMountPermissionAction(
            vfolder_id=vfolder_uuid,
            user_id=user_id,
            permission=VFolderMountPermission.RW_DELETE,
        )
        result = await invite_service.update_invited_vfolder_mount_permission(action)

        assert result.vfolder_id == vfolder_uuid
        assert result.user_id == user_id
        assert result.permission == VFolderMountPermission.RW_DELETE
        mock_vfolder_repo.update_invited_vfolder_mount_permission.assert_called_once_with(
            vfolder_uuid, user_id, VFolderMountPermission.RW_DELETE
        )
