"""
Simple tests for VFolder Invitation Service functionality.
Tests the core invitation service actions to verify compatibility with test scenarios.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.storage import (
    VFolderGrantAlreadyExists,
    VFolderInvitationNotFound,
    VFolderPermissionError,
)
from ai.backend.manager.models.vfolder import VFolderInvitationState, VFolderPermission
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    InviteVFolderAction,
    LeaveInvitedVFolderAction,
    ListInvitationAction,
    RejectInvitationAction,
    UpdateInvitationAction,
)
from ai.backend.manager.services.vfolder.processors.invite import VFolderInviteProcessors
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService
from ai.backend.manager.services.vfolder.types import VFolderInvitationInfo


class TestInviteServiceCompatibility:
    """Test compatibility of invitation service with test scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        vfolder_repository = MagicMock(spec=VfolderRepository)
        admin_vfolder_repository = MagicMock(spec=AdminVfolderRepository)
        admin_user_repository = MagicMock(spec=AdminUserRepository)
        action_monitor = MagicMock(spec=ActionMonitor)

        return {
            "config_provider": config_provider,
            "vfolder_repository": vfolder_repository,
            "admin_vfolder_repository": admin_vfolder_repository,
            "admin_user_repository": admin_user_repository,
            "action_monitor": action_monitor,
        }

    @pytest.fixture
    def invite_service(self, mock_dependencies):
        """Create VFolderInviteService instance with mocked dependencies."""
        return VFolderInviteService(
            config_provider=mock_dependencies["config_provider"],
            vfolder_repository=mock_dependencies["vfolder_repository"],
            admin_vfolder_repository=mock_dependencies["admin_vfolder_repository"],
        )

    @pytest.fixture
    def invite_processors(self, invite_service, mock_dependencies):
        """Create VFolderInviteProcessors instance."""
        return VFolderInviteProcessors(
            service=invite_service,
            action_monitors=[mock_dependencies["action_monitor"]],
        )

    @pytest.mark.asyncio
    async def test_invite_readonly_permission(self, invite_processors, mock_dependencies):
        """Test 5.1: Read-only permission invitation - Data sharing."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        invitee_id = uuid.uuid4()
        invitation_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,  # Owner
            "permission": "rw",
        }
        mock_dependencies["admin_vfolder_repository"].invite.return_value = [invitation_id]

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=owner_id,
            vfolder_uuid=vfolder_id,
            mount_permission=VFolderPermission.READ_ONLY,
            invitee_user_uuids=[invitee_id],
        )

        result = await invite_processors.invite_vfolder(action)

        assert result.vfolder_uuid == vfolder_id
        assert len(result.invitation_ids) == 1
        assert result.invitation_ids[0] == invitation_id
        mock_dependencies["admin_vfolder_repository"].invite.assert_called_once()

    @pytest.mark.asyncio
    async def test_invite_readwrite_permission(self, invite_processors, mock_dependencies):
        """Test 5.2: Read-write permission invitation - Collaboration support."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        invitee_id = uuid.uuid4()
        invitation_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,
            "permission": "rw",
        }
        mock_dependencies["admin_vfolder_repository"].invite.return_value = [invitation_id]

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=owner_id,
            vfolder_uuid=vfolder_id,
            mount_permission=VFolderPermission.READ_WRITE,
            invitee_user_uuids=[invitee_id],
        )

        result = await invite_processors.invite_vfolder(action)

        assert result.vfolder_uuid == vfolder_id
        assert result.invitation_ids == [invitation_id]

    @pytest.mark.asyncio
    async def test_invite_full_permission(self, invite_processors, mock_dependencies):
        """Test 5.3: Full permission including delete - Complete control."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        invitee_id = uuid.uuid4()
        invitation_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,
            "permission": "rwd",
        }
        mock_dependencies["admin_vfolder_repository"].invite.return_value = [invitation_id]

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=owner_id,
            vfolder_uuid=vfolder_id,
            mount_permission=VFolderPermission.RW_DELETE,
            invitee_user_uuids=[invitee_id],
        )

        result = await invite_processors.invite_vfolder(action)

        assert result.vfolder_uuid == vfolder_id
        assert result.invitation_ids == [invitation_id]

    @pytest.mark.asyncio
    async def test_invite_bulk_users(self, invite_processors, mock_dependencies):
        """Test 5.4: Bulk invitation - Team sharing."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        invitee_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        invitation_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,
            "permission": "rw",
        }
        mock_dependencies["admin_vfolder_repository"].invite.return_value = invitation_ids

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=owner_id,
            vfolder_uuid=vfolder_id,
            mount_permission=VFolderPermission.READ_WRITE,
            invitee_user_uuids=invitee_ids,
        )

        result = await invite_processors.invite_vfolder(action)

        assert result.vfolder_uuid == vfolder_id
        assert len(result.invitation_ids) == 3
        assert result.invitation_ids == invitation_ids

    @pytest.mark.asyncio
    async def test_invite_duplicate_user(self, invite_processors, mock_dependencies):
        """Test 5.5: Duplicate invitation - Already invited user."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        invitee_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,
        }
        mock_dependencies["admin_vfolder_repository"].invite.side_effect = VFolderGrantAlreadyExists

        action = InviteVFolderAction(
            keypair_resource_policy={},
            user_uuid=owner_id,
            vfolder_uuid=vfolder_id,
            mount_permission=VFolderPermission.READ_WRITE,
            invitee_user_uuids=[invitee_id],
        )

        with pytest.raises(VFolderGrantAlreadyExists):
            await invite_processors.invite_vfolder(action)

    @pytest.mark.asyncio
    async def test_accept_invitation_success(self, invite_processors, mock_dependencies):
        """Test Invitation Acceptance - Normal acceptance."""
        invitation_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["admin_vfolder_repository"].accept_invitation.return_value = None

        action = AcceptInvitationAction(invitation_id=invitation_id)

        result = await invite_processors.accept_invitation(action)

        assert result.invitation_id == invitation_id
        mock_dependencies["admin_vfolder_repository"].accept_invitation.assert_called_once()

    @pytest.mark.asyncio
    async def test_accept_invitation_not_found(self, invite_processors, mock_dependencies):
        """Test Invitation Acceptance - Non-existent invitation."""
        invitation_id = uuid.uuid4()

        # Setup mock
        mock_dependencies[
            "admin_vfolder_repository"
        ].accept_invitation.side_effect = VFolderInvitationNotFound

        action = AcceptInvitationAction(invitation_id=invitation_id)

        with pytest.raises(VFolderInvitationNotFound):
            await invite_processors.accept_invitation(action)

    @pytest.mark.asyncio
    async def test_reject_invitation(self, invite_processors, mock_dependencies):
        """Test Invitation Rejection - Normal rejection."""
        invitation_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["admin_vfolder_repository"].reject_invitation.return_value = None

        action = RejectInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=user_id,
        )

        result = await invite_processors.reject_invitation(action)

        assert result.invitation_id == invitation_id
        mock_dependencies["admin_vfolder_repository"].reject_invitation.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_invitation_permission(self, invite_processors, mock_dependencies):
        """Test Invitation Update - Change from read-only to read-write."""
        invitation_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["admin_vfolder_repository"].update_invitation.return_value = None

        action = UpdateInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=owner_id,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        result = await invite_processors.update_invitation(action)

        assert result.invitation_id == invitation_id
        mock_dependencies["admin_vfolder_repository"].update_invitation.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_invitation_no_permission(self, invite_processors, mock_dependencies):
        """Test Invitation Update - No permission to update."""
        invitation_id = uuid.uuid4()
        non_owner_id = uuid.uuid4()

        # Setup mock
        mock_dependencies[
            "admin_vfolder_repository"
        ].update_invitation.side_effect = VFolderPermissionError

        action = UpdateInvitationAction(
            invitation_id=invitation_id,
            requester_user_uuid=non_owner_id,
            mount_permission=VFolderPermission.RW_DELETE,
        )

        with pytest.raises(VFolderPermissionError):
            await invite_processors.update_invitation(action)

    @pytest.mark.asyncio
    async def test_list_invitations(self, invite_processors, mock_dependencies):
        """Test List Invitations - View pending invitations."""
        user_id = uuid.uuid4()
        invitations = [
            VFolderInvitationInfo(
                id=uuid.uuid4(),
                vfolder_id=uuid.uuid4(),
                vfolder_name="shared-data",
                inviter_user_email="owner@example.com",
                invitee_user_email="user@example.com",
                mount_permission=VFolderPermission.READ_ONLY,
                created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
                modified_at=None,
                status=VFolderInvitationState.PENDING,
            ),
            VFolderInvitationInfo(
                id=uuid.uuid4(),
                vfolder_id=uuid.uuid4(),
                vfolder_name="team-project",
                inviter_user_email="lead@example.com",
                invitee_user_email="user@example.com",
                mount_permission=VFolderPermission.READ_WRITE,
                created_at=datetime.fromisoformat("2024-01-02T00:00:00Z"),
                modified_at=None,
                status=VFolderInvitationState.PENDING,
            ),
        ]

        # Setup mock
        mock_dependencies["vfolder_repository"].list_invitations.return_value = invitations

        action = ListInvitationAction(requester_user_uuid=user_id)

        result = await invite_processors.list_invitation(action)

        assert result.requester_user_uuid == user_id
        assert len(result.info) == 2
        assert result.info[0].vfolder_name == "shared-data"
        assert result.info[1].vfolder_name == "team-project"

    @pytest.mark.asyncio
    async def test_leave_invited_vfolder_self(self, invite_processors, mock_dependencies):
        """Test Leave Shared VFolder - User leaves by themselves."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["admin_vfolder_repository"].leave_invited_vfolder.return_value = None

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_id,
            requester_user_uuid=user_id,
            shared_user_uuid=None,  # User leaving themselves
        )

        result = await invite_processors.leave_invited_vfolder(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].leave_invited_vfolder.assert_called_once()

    @pytest.mark.asyncio
    async def test_leave_invited_vfolder_remove_user(self, invite_processors, mock_dependencies):
        """Test Leave Shared VFolder - Owner removes specific user."""
        vfolder_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        shared_user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": owner_id,  # Requester is owner
        }
        mock_dependencies["admin_vfolder_repository"].leave_invited_vfolder.return_value = None

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_id,
            requester_user_uuid=owner_id,
            shared_user_uuid=shared_user_id,
        )

        result = await invite_processors.leave_invited_vfolder(action)

        assert result.vfolder_uuid == vfolder_id

    @pytest.mark.asyncio
    async def test_leave_invited_vfolder_no_permission(self, invite_processors, mock_dependencies):
        """Test Leave Shared VFolder - No permission to remove user."""
        vfolder_id = uuid.uuid4()
        non_owner_id = uuid.uuid4()
        shared_user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": uuid.uuid4(),  # Different owner
        }

        action = LeaveInvitedVFolderAction(
            vfolder_uuid=vfolder_id,
            requester_user_uuid=non_owner_id,
            shared_user_uuid=shared_user_id,
        )

        with pytest.raises(VFolderPermissionError):
            await invite_processors.leave_invited_vfolder(action)
