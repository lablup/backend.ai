import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.unified import ConfigProvider
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.repositories.user.admin_user_repository import AdminUserRepository
from ai.backend.manager.repositories.vfolder.admin_vfolder_repository import AdminVFolderRepository
from ai.backend.manager.repositories.vfolder.vfolder_repository import VFolderRepository
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
)
from ai.backend.manager.services.vfolder.exceptions import (
    VFolderAlreadySharedError,
    VFolderInvitationNotFoundError,
    VFolderPermissionError,
)
from ai.backend.manager.services.vfolder.processors.invite import InviteProcessors
from ai.backend.manager.services.vfolder.services.invite import InviteService
from ai.backend.manager.services.vfolder.types import VFolderInvitationInfo

from ..test_utils import TestScenario


@pytest.fixture
def mock_config_provider():
    return MagicMock(spec=ConfigProvider)


@pytest.fixture
def mock_vfolder_repository():
    return MagicMock(spec=VFolderRepository)


@pytest.fixture
def mock_admin_vfolder_repository():
    return MagicMock(spec=AdminVFolderRepository)


@pytest.fixture
def mock_admin_user_repository():
    return MagicMock(spec=AdminUserRepository)


@pytest.fixture
def mock_action_monitor():
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def invite_service(
    mock_config_provider,
    mock_vfolder_repository,
    mock_admin_vfolder_repository,
    mock_admin_user_repository,
):
    return InviteService(
        config_provider=mock_config_provider,
        vfolder_repository=mock_vfolder_repository,
        admin_vfolder_repository=mock_admin_vfolder_repository,
        admin_user_repository=mock_admin_user_repository,
    )


@pytest.fixture
def invite_processors(invite_service, mock_action_monitor):
    return InviteProcessors(invite_service=invite_service, action_monitors=[mock_action_monitor])


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "5.1 읽기 권한 초대 - 데이터 공유",
            InviteVFolderAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.READ_ONLY,
                invitee_user_uuids=[uuid.uuid4()],
            ),
            InviteVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
                invitation_ids=[uuid.uuid4()],
            ),
        ),
        TestScenario.success(
            "5.2 쓰기 권한 초대 - 협업 지원",
            InviteVFolderAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.READ_WRITE,
                invitee_user_uuids=[uuid.uuid4()],
            ),
            InviteVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
                invitation_ids=[uuid.uuid4()],
            ),
        ),
        TestScenario.success(
            "5.3 삭제 권한 포함 - 완전한 제어권",
            InviteVFolderAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.RW_DELETE,
                invitee_user_uuids=[uuid.uuid4()],
            ),
            InviteVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
                invitation_ids=[uuid.uuid4()],
            ),
        ),
        TestScenario.success(
            "5.4 대량 초대 - 팀 전체 공유",
            InviteVFolderAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.READ_WRITE,
                invitee_user_uuids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
            ),
            InviteVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
                invitation_ids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
            ),
        ),
        TestScenario.failure(
            "5.5 중복 초대 - 이미 초대된 사용자",
            InviteVFolderAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.READ_WRITE,
                invitee_user_uuids=[uuid.uuid4()],  # Already invited user
            ),
            VFolderAlreadySharedError,
        ),
    ],
)
async def test_invite_to_vfolder(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[InviteVFolderAction, InviteVFolderActionResult],
):
    """Test VFolder invitation functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "user": test_scenario.input.user_uuid,  # Owner
            "permission": "rw",
        }

        # Mock successful invitation creation
        invitation_ids = test_scenario.expected.invitation_ids
        mock_admin_vfolder_repository.invite.return_value = invitation_ids
    else:
        # Setup mock for failure case - already shared
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "user": test_scenario.input.user_uuid,
        }
        mock_admin_vfolder_repository.invite.side_effect = VFolderAlreadySharedError

    await test_scenario.test(invite_processors.invite)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "초대 수락 - 정상적인 초대 수락",
            AcceptInvitationAction(
                invitation_id=uuid.uuid4(),
            ),
            AcceptInvitationActionResult(
                invitation_id=uuid.uuid4(),
            ),
        ),
        TestScenario.failure(
            "초대 수락 - 존재하지 않는 초대",
            AcceptInvitationAction(
                invitation_id=uuid.uuid4(),
            ),
            VFolderInvitationNotFoundError,
        ),
    ],
)
async def test_accept_invitation(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[AcceptInvitationAction, AcceptInvitationActionResult],
):
    """Test invitation acceptance functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_admin_vfolder_repository.accept_invitation.return_value = None
    else:
        # Setup mock for failure case
        mock_admin_vfolder_repository.accept_invitation.side_effect = VFolderInvitationNotFoundError

    await test_scenario.test(invite_processors.accept_invitation)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "초대 거절 - 정상적인 초대 거절",
            RejectInvitationAction(
                invitation_id=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),
            ),
            RejectInvitationActionResult(
                invitation_id=uuid.uuid4(),
            ),
        ),
    ],
)
async def test_reject_invitation(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[RejectInvitationAction, RejectInvitationActionResult],
):
    """Test invitation rejection functionality"""
    # Setup mock
    mock_admin_vfolder_repository.reject_invitation.return_value = None

    await test_scenario.test(invite_processors.reject_invitation)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "초대 권한 수정 - 읽기 전용에서 읽기/쓰기로 변경",
            UpdateInvitationAction(
                invitation_id=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),
                mount_permission=VFolderPermission.READ_WRITE,
            ),
            UpdateInvitationActionResult(
                invitation_id=uuid.uuid4(),
            ),
        ),
        TestScenario.failure(
            "초대 권한 수정 - 권한 없음",
            UpdateInvitationAction(
                invitation_id=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),  # Not the owner
                mount_permission=VFolderPermission.RW_DELETE,
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_update_invitation(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[UpdateInvitationAction, UpdateInvitationActionResult],
):
    """Test invitation update functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_admin_vfolder_repository.update_invitation.return_value = None
    else:
        # Setup mock for failure case - not authorized
        mock_admin_vfolder_repository.update_invitation.side_effect = VFolderPermissionError

    await test_scenario.test(invite_processors.update_invitation)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "초대 목록 조회 - 받은 초대 목록",
            ListInvitationAction(
                requester_user_uuid=uuid.uuid4(),
            ),
            ListInvitationActionResult(
                requester_user_uuid=uuid.uuid4(),
                info=[
                    VFolderInvitationInfo(
                        invitation_id=uuid.uuid4(),
                        vfolder_id=uuid.uuid4(),
                        vfolder_name="shared-data",
                        inviter_email="owner@example.com",
                        invitee_email="user@example.com",
                        mount_permission=VFolderPermission.READ_ONLY,
                        created_at="2024-01-01T00:00:00Z",
                    ),
                    VFolderInvitationInfo(
                        invitation_id=uuid.uuid4(),
                        vfolder_id=uuid.uuid4(),
                        vfolder_name="team-project",
                        inviter_email="lead@example.com",
                        invitee_email="user@example.com",
                        mount_permission=VFolderPermission.READ_WRITE,
                        created_at="2024-01-02T00:00:00Z",
                    ),
                ],
            ),
        ),
    ],
)
async def test_list_invitations(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[ListInvitationAction, ListInvitationActionResult],
):
    """Test invitation listing functionality"""
    # Setup mock
    mock_vfolder_repository.list_invitations.return_value = test_scenario.expected.info

    await test_scenario.test(invite_processors.list_invitations)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "공유 폴더 나가기 - 사용자가 공유 폴더에서 나감",
            LeaveInvitedVFolderAction(
                vfolder_uuid=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),
                shared_user_uuid=None,  # Current user leaves
            ),
            LeaveInvitedVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
        TestScenario.success(
            "공유 폴더에서 사용자 제거 - 소유자가 특정 사용자 제거",
            LeaveInvitedVFolderAction(
                vfolder_uuid=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),  # Owner
                shared_user_uuid=uuid.uuid4(),  # User to remove
            ),
            LeaveInvitedVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
        TestScenario.failure(
            "공유 폴더 나가기 - 권한 없음",
            LeaveInvitedVFolderAction(
                vfolder_uuid=uuid.uuid4(),
                requester_user_uuid=uuid.uuid4(),  # Not owner
                shared_user_uuid=uuid.uuid4(),  # Trying to remove another user
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_leave_invited_vfolder(
    invite_processors: InviteProcessors,
    invite_service: InviteService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult],
):
    """Test leaving shared VFolder functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        if test_scenario.input.shared_user_uuid is None:
            # User leaving themselves
            mock_admin_vfolder_repository.leave_invited_vfolder.return_value = None
        else:
            # Owner removing another user
            mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
                "id": test_scenario.input.vfolder_uuid,
                "user": test_scenario.input.requester_user_uuid,  # Requester is owner
            }
            mock_admin_vfolder_repository.leave_invited_vfolder.return_value = None
    else:
        # Setup mock for failure case - not authorized
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "user": uuid.uuid4(),  # Different owner
        }

    await test_scenario.test(invite_processors.leave_invited_vfolder)
