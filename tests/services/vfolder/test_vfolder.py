import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.client_context import ClientContext
from ai.backend.manager.config.unified import ConfigProvider
from ai.backend.manager.models.resource_policy import KeypairResourcePolicyRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.repositories.quota import QuotaRepository
from ai.backend.manager.repositories.vfolder.admin_vfolder_repository import AdminVFolderRepository
from ai.backend.manager.repositories.vfolder.vfolder_repository import VFolderRepository
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetTaskLogsAction,
    GetTaskLogsActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
    VFolderAttributeModifier,
)
from ai.backend.manager.services.vfolder.exceptions import (
    VFolderAlreadyExistsError,
    VFolderInUseError,
    VFolderNotCloneableError,
    VFolderNotFoundError,
    VFolderPermissionError,
    VFolderQuotaExceededError,
)
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.services.vfolder.types import (
    VFolderBaseInfo,
    VFolderOwnershipInfo,
    VFolderUsageInfo,
)
from ai.backend.manager.types import OptionalState

from ..test_utils import TestScenario


@pytest.fixture
def mock_config_provider():
    return MagicMock(spec=ConfigProvider)


@pytest.fixture
def mock_storage_manager():
    return MagicMock(spec=StorageSessionManager)


@pytest.fixture
def mock_vfolder_repository():
    return MagicMock(spec=VFolderRepository)


@pytest.fixture
def mock_admin_vfolder_repository():
    return MagicMock(spec=AdminVFolderRepository)


@pytest.fixture
def mock_quota_repository():
    return MagicMock(spec=QuotaRepository)


@pytest.fixture
def mock_client_context():
    return MagicMock(spec=ClientContext)


@pytest.fixture
def mock_action_monitor():
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def vfolder_service(
    mock_config_provider,
    mock_storage_manager,
    mock_vfolder_repository,
    mock_admin_vfolder_repository,
    mock_quota_repository,
    mock_client_context,
):
    return VFolderService(
        config_provider=mock_config_provider,
        storage_manager=mock_storage_manager,
        vfolder_repository=mock_vfolder_repository,
        admin_vfolder_repository=mock_admin_vfolder_repository,
        quota_repository=mock_quota_repository,
        client_context=mock_client_context,
    )


@pytest.fixture
def vfolder_processors(vfolder_service, mock_action_monitor):
    return VFolderProcessors(vfolder_service=vfolder_service, action_monitors=[mock_action_monitor])


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "1.1 개인 VFolder 생성 - 개인 작업 공간 생성",
            CreateVFolderAction(
                name="my-workspace",
                keypair_resource_policy={"max_vfolder_size": 10737418240},
                domain_name="default",
                group_id_or_name=None,
                folder_host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.GENERAL,
                cloneable=False,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.USER,
                creator_email="user@example.com",
            ),
            CreateVFolderActionResult(
                id=uuid.uuid4(),
                name="my-workspace",
                quota_scope_id=QuotaScopeID("12345"),
                host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.GENERAL,
                creator_email="user@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user_uuid=uuid.uuid4(),
                group_uuid=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            ),
        ),
        TestScenario.success(
            "1.2 프로젝트 VFolder 생성 - 팀 공유 스토리지",
            CreateVFolderAction(
                name="team-data",
                keypair_resource_policy={"max_vfolder_size": 107374182400},
                domain_name="default",
                group_id_or_name=uuid.uuid4(),  # Project ID
                folder_host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.DATA,
                cloneable=True,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.USER,
                creator_email="team@example.com",
            ),
            CreateVFolderActionResult(
                id=uuid.uuid4(),
                name="team-data",
                quota_scope_id=QuotaScopeID("67890"),
                host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.DATA,
                creator_email="team@example.com",
                ownership_type=VFolderOwnershipType.GROUP,
                user_uuid=None,
                group_uuid=uuid.uuid4(),
                cloneable=True,
                status=VFolderOperationStatus.READY,
            ),
        ),
        TestScenario.success(
            "1.3 모델 저장소 생성 - 모델 배포용 스토리지",
            CreateVFolderAction(
                name="ml-models",
                keypair_resource_policy={"max_vfolder_size": 53687091200},
                domain_name="default",
                group_id_or_name=None,
                folder_host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_ONLY,
                usage_mode=VFolderUsageMode.MODEL,
                cloneable=False,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.USER,
                creator_email="ml@example.com",
            ),
            CreateVFolderActionResult(
                id=uuid.uuid4(),
                name="ml-models",
                quota_scope_id=QuotaScopeID("11111"),
                host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_ONLY,
                usage_mode=VFolderUsageMode.MODEL,
                creator_email="ml@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user_uuid=uuid.uuid4(),
                group_uuid=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            ),
        ),
        TestScenario.failure(
            "1.4 중복 이름 - 소유자별 고유 이름",
            CreateVFolderAction(
                name="existing-folder",
                keypair_resource_policy={"max_vfolder_size": 10737418240},
                domain_name="default",
                group_id_or_name=None,
                folder_host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.GENERAL,
                cloneable=False,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.USER,
                creator_email="user@example.com",
            ),
            VFolderAlreadyExistsError,
        ),
        TestScenario.failure(
            "1.5 할당량 초과 - 리소스 정책 준수",
            CreateVFolderAction(
                name="large-folder",
                keypair_resource_policy={"max_vfolder_size": 1099511627776},  # 1TB limit
                domain_name="default",
                group_id_or_name=None,
                folder_host="storage1",
                unmanaged_path=None,
                mount_permission=VFolderPermission.READ_WRITE,
                usage_mode=VFolderUsageMode.GENERAL,
                cloneable=False,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.USER,
                creator_email="user@example.com",
            ),
            VFolderQuotaExceededError,
        ),
        TestScenario.success(
            "1.6 Unmanaged VFolder - 기존 데이터 접근",
            CreateVFolderAction(
                name="external-data",
                keypair_resource_policy={"max_vfolder_size": 0},  # No quota for unmanaged
                domain_name="default",
                group_id_or_name=None,
                folder_host="storage1",
                unmanaged_path="/mnt/external/data",
                mount_permission=VFolderPermission.READ_ONLY,
                usage_mode=VFolderUsageMode.DATA,
                cloneable=False,
                user_uuid=uuid.uuid4(),
                user_role=UserRole.ADMIN,  # Admin only
                creator_email="admin@example.com",
            ),
            CreateVFolderActionResult(
                id=uuid.uuid4(),
                name="external-data",
                quota_scope_id=QuotaScopeID("unmanaged"),
                host="storage1",
                unmanaged_path="/mnt/external/data",
                mount_permission=VFolderPermission.READ_ONLY,
                usage_mode=VFolderUsageMode.DATA,
                creator_email="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user_uuid=uuid.uuid4(),
                group_uuid=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            ),
        ),
    ],
)
async def test_create_vfolder(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    mock_quota_repository: MagicMock,
    test_scenario: TestScenario[CreateVFolderAction, CreateVFolderActionResult],
):
    """Test VFolder creation functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_name.return_value = None  # No existing folder
        mock_quota_repository.check_quota.return_value = True
        mock_admin_vfolder_repository.create.return_value = test_scenario.expected
    else:
        if test_scenario.expected_exception == VFolderAlreadyExistsError:
            # Setup mock for duplicate name
            mock_vfolder_repository.get_vfolder_by_name.return_value = {"id": uuid.uuid4()}
        elif test_scenario.expected_exception == VFolderQuotaExceededError:
            # Setup mock for quota exceeded
            mock_vfolder_repository.get_vfolder_by_name.return_value = None
            mock_quota_repository.check_quota.return_value = False

    await test_scenario.test(vfolder_processors.create)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "2. VFolder 속성 수정 - 이름 변경",
            UpdateVFolderAttributeAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                modifier=VFolderAttributeModifier(
                    name=OptionalState.set("renamed-folder"),
                ),
            ),
            UpdateVFolderAttributeActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
        TestScenario.success(
            "2. VFolder 속성 수정 - 복제 가능 설정",
            UpdateVFolderAttributeAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                modifier=VFolderAttributeModifier(
                    cloneable=OptionalState.set(True),
                ),
            ),
            UpdateVFolderAttributeActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
        TestScenario.success(
            "2. VFolder 속성 수정 - 권한 변경",
            UpdateVFolderAttributeAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                modifier=VFolderAttributeModifier(
                    mount_permission=OptionalState.set(VFolderPermission.RW_DELETE),
                ),
            ),
            UpdateVFolderAttributeActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
    ],
)
async def test_update_vfolder_attribute(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[UpdateVFolderAttributeAction, UpdateVFolderAttributeActionResult],
):
    """Test VFolder attribute update functionality"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "user": test_scenario.input.user_uuid,
    }
    mock_admin_vfolder_repository.update_attribute.return_value = None

    await test_scenario.test(vfolder_processors.update_attribute)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "3. VFolder 정보 조회 - 사용량 포함",
            GetVFolderAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
            ),
            GetVFolderActionResult(
                user_uuid=uuid.uuid4(),
                base_info=VFolderBaseInfo(
                    id=uuid.uuid4(),
                    name="my-vfolder",
                    host="storage1",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderPermission.READ_WRITE,
                    ownership_type=VFolderOwnershipType.USER,
                    status=VFolderOperationStatus.READY,
                    quota=10737418240,  # 10GB
                    cloneable=False,
                ),
                ownership_info=VFolderOwnershipInfo(
                    owner_user_uuid=uuid.uuid4(),
                    owner_user_email="user@example.com",
                    owner_user_name="User Name",
                    owner_group_uuid=None,
                    owner_group_name=None,
                ),
                usage_info=VFolderUsageInfo(
                    used_bytes=1073741824,  # 1GB
                    file_count=100,
                ),
            ),
        ),
    ],
)
async def test_get_vfolder(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[GetVFolderAction, GetVFolderActionResult],
):
    """Test VFolder information retrieval"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "user": test_scenario.input.user_uuid,
        "name": test_scenario.expected.base_info.name,
        "host": test_scenario.expected.base_info.host,
        "usage_mode": test_scenario.expected.base_info.usage_mode,
        "permission": test_scenario.expected.base_info.permission,
        "ownership_type": test_scenario.expected.base_info.ownership_type,
        "status": test_scenario.expected.base_info.status,
        "max_size": test_scenario.expected.base_info.quota,
        "cloneable": test_scenario.expected.base_info.cloneable,
    }

    # Mock usage info
    vfolder_service.storage_manager.get_usage.return_value = AsyncMock(
        return_value=(
            test_scenario.expected.usage_info.used_bytes,
            test_scenario.expected.usage_info.file_count,
        )
    )()

    await test_scenario.test(vfolder_processors.get)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "4.1 전체 복제 - 백업 또는 실험",
            CloneVFolderAction(
                requester_user_uuid=uuid.uuid4(),
                source_vfolder_uuid=uuid.uuid4(),
                target_name="cloned-folder",
                target_host="storage1",
                cloneable=True,
                usage_mode=VFolderUsageMode.GENERAL,
                mount_permission=VFolderPermission.READ_WRITE,
            ),
            CloneVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
                target_vfolder_id=uuid.uuid4(),
                target_vfolder_name="cloned-folder",
                target_vfolder_host="storage1",
                usage_mode=VFolderUsageMode.GENERAL,
                mount_permission=VFolderPermission.READ_WRITE,
                creator_email="user@example.com",
                ownership_type=VFolderOwnershipType.USER,
                owner_user_uuid=uuid.uuid4(),
                owner_group_uuid=None,
                cloneable=True,
                bgtask_id=uuid.uuid4(),
            ),
        ),
        TestScenario.failure(
            "4.3 권한 없는 복제 - 복제 권한 제어",
            CloneVFolderAction(
                requester_user_uuid=uuid.uuid4(),
                source_vfolder_uuid=uuid.uuid4(),
                target_name="unauthorized-clone",
                target_host="storage1",
                cloneable=False,  # Not cloneable
                usage_mode=VFolderUsageMode.GENERAL,
                mount_permission=VFolderPermission.READ_WRITE,
            ),
            VFolderNotCloneableError,
        ),
    ],
)
async def test_clone_vfolder(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[CloneVFolderAction, CloneVFolderActionResult],
):
    """Test VFolder cloning functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.source_vfolder_uuid,
            "cloneable": True,
            "host": "storage1",
        }
        # Mock the clone operation
        mock_admin_vfolder_repository.clone.return_value = test_scenario.expected
    else:
        # Setup mock for failure case - not cloneable
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.source_vfolder_uuid,
            "cloneable": False,
            "host": "storage1",
        }

    await test_scenario.test(vfolder_processors.clone)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "6.1 정상적인 삭제 - 실수 방지",
            MoveToTrashVFolderAction(
                user_uuid=uuid.uuid4(),
                keypair_resource_policy={},
                vfolder_uuid=uuid.uuid4(),
            ),
            MoveToTrashVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
        TestScenario.failure(
            "6.2 마운트된 VFolder - 사용 중 보호",
            MoveToTrashVFolderAction(
                user_uuid=uuid.uuid4(),
                keypair_resource_policy={},
                vfolder_uuid=uuid.uuid4(),
            ),
            VFolderInUseError,
        ),
    ],
)
async def test_move_to_trash(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[MoveToTrashVFolderAction, MoveToTrashVFolderActionResult],
):
    """Test moving VFolder to trash"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "user": test_scenario.input.user_uuid,
            "status": VFolderOperationStatus.READY,
        }
        mock_vfolder_repository.is_vfolder_mounted.return_value = False
        mock_admin_vfolder_repository.move_to_trash.return_value = None
    else:
        # Setup mock for failure case - VFolder in use
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "user": test_scenario.input.user_uuid,
            "status": VFolderOperationStatus.READY,
        }
        mock_vfolder_repository.is_vfolder_mounted.return_value = True

    await test_scenario.test(vfolder_processors.move_to_trash)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "휴지통에서 복원 - VFolder 복구",
            RestoreVFolderFromTrashAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
            ),
            RestoreVFolderFromTrashActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
    ],
)
async def test_restore_from_trash(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[RestoreVFolderFromTrashAction, RestoreVFolderFromTrashActionResult],
):
    """Test restoring VFolder from trash"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "user": test_scenario.input.user_uuid,
        "status": VFolderOperationStatus.DELETE_PENDING,
    }
    mock_admin_vfolder_repository.restore_from_trash.return_value = None

    await test_scenario.test(vfolder_processors.restore_from_trash)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "영구 삭제 - 휴지통에서 완전 제거",
            DeleteForeverVFolderAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
            ),
            DeleteForeverVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
    ],
)
async def test_delete_forever(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[DeleteForeverVFolderAction, DeleteForeverVFolderActionResult],
):
    """Test permanent VFolder deletion"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "user": test_scenario.input.user_uuid,
        "status": VFolderOperationStatus.DELETE_PENDING,
    }
    mock_admin_vfolder_repository.delete_forever.return_value = None

    await test_scenario.test(vfolder_processors.delete_forever)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "강제 삭제 - 즉시 영구 삭제",
            ForceDeleteVFolderAction(
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
            ),
            ForceDeleteVFolderActionResult(
                vfolder_uuid=uuid.uuid4(),
            ),
        ),
    ],
)
async def test_force_delete(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    mock_vfolder_repository: MagicMock,
    mock_admin_vfolder_repository: MagicMock,
    test_scenario: TestScenario[ForceDeleteVFolderAction, ForceDeleteVFolderActionResult],
):
    """Test force deletion of VFolder"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "user": test_scenario.input.user_uuid,
        "status": VFolderOperationStatus.READY,
    }
    mock_admin_vfolder_repository.force_delete.return_value = None

    await test_scenario.test(vfolder_processors.force_delete)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "7.1 복제 작업 로그 - 장시간 작업 추적",
            GetTaskLogsAction(
                user_id=uuid.uuid4(),
                domain_name="default",
                user_role=UserRole.USER,
                kernel_id="task-kernel-id",
                owner_access_key="user-access-key",
                request=MagicMock(),
            ),
            GetTaskLogsActionResult(
                response={
                    "task_id": str(uuid.uuid4()),
                    "status": "completed",
                    "progress": 100,
                    "logs": ["Cloning started", "Files copied: 1000", "Clone completed"],
                },
                vfolder_data={"id": str(uuid.uuid4())},
            ),
        ),
    ],
)
async def test_get_task_logs(
    vfolder_processors: VFolderProcessors,
    vfolder_service: VFolderService,
    test_scenario: TestScenario[GetTaskLogsAction, GetTaskLogsActionResult],
):
    """Test task log retrieval"""
    # Note: Current implementation returns placeholder data
    # This test verifies the interface works correctly
    await test_scenario.test(vfolder_processors.get_task_logs)
