"""
Tests for VFolderService and VFolderFileService functionality.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.common.types import QuotaScopeID, VFolderID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    ValidatedVFolderInfo,
    VFolderAccessInfo,
    VFolderData,
    VFolderListResult,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.storage import (
    VFolderFilterStatusFailed,
    VFolderNotFound,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import VFolderPermission, VFolderRow
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.vfolder.purgers import VFolderPurgerSpec
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    PurgeVFolderAction,
    PurgeVFolderActionResult,
)
from ai.backend.manager.services.vfolder.actions.file import (
    CreateArchiveDownloadSessionAction,
    CreateArchiveDownloadSessionActionResult,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


@pytest.fixture
def sample_vfolder_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_vfolder_data(sample_vfolder_uuid: uuid.UUID) -> VFolderData:
    return VFolderData(
        id=sample_vfolder_uuid,
        name="test-vfolder",
        host="local:volume1",
        domain_name="default",
        quota_scope_id=QuotaScopeID.parse(f"user:{sample_vfolder_uuid}"),
        usage_mode=VFolderUsageMode.GENERAL,
        permission=VFolderMountPermission.READ_WRITE,
        max_files=0,
        max_size=None,
        num_files=0,
        cur_size=0,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        last_used=None,
        creator="test@example.com",
        unmanaged_path=None,
        ownership_type=VFolderOwnershipType.USER,
        user=sample_vfolder_uuid,
        group=None,
        cloneable=False,
        status=VFolderOperationStatus.READY,
    )


@pytest.fixture
def mock_vfolder_repository() -> MagicMock:
    return MagicMock(spec=VfolderRepository)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(return_value=["user"])
    return provider


class TestVFolderServicePurge:
    """Tests for VFolderService.purge() method.

    Note: Validation logic (not found, invalid status) is tested in repository tests.
    Service tests verify that the repository method is called correctly and
    exceptions are propagated.
    """

    @pytest.fixture
    def vfolder_service(self, mock_vfolder_repository: MagicMock) -> VFolderService:
        return VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=MagicMock(),
            background_task_manager=MagicMock(),
            vfolder_repository=mock_vfolder_repository,
            user_repository=MagicMock(),
            valkey_stat_client=MagicMock(),
        )

    @pytest.fixture
    def sample_purger(self, sample_vfolder_uuid: uuid.UUID) -> RBACEntityPurger[VFolderRow]:
        return RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=sample_vfolder_uuid,
            spec=VFolderPurgerSpec(vfolder_id=sample_vfolder_uuid),
        )

    @pytest.fixture
    def sample_action(self, sample_purger: RBACEntityPurger[VFolderRow]) -> PurgeVFolderAction:
        return PurgeVFolderAction(purger=sample_purger)

    async def test_purge_vfolder_success(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_action: PurgeVFolderAction,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """Test successful purge of vfolder."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(return_value=sample_vfolder_data)

        result = await vfolder_service.purge(sample_action)

        assert isinstance(result, PurgeVFolderActionResult)
        assert result.vfolder_uuid == sample_vfolder_uuid
        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)

    async def test_purge_vfolder_not_found_propagates(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_action: PurgeVFolderAction,
    ) -> None:
        """Test that VFolderNotFound from repository is propagated."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(
            side_effect=VFolderNotFound(extra_data=str(sample_vfolder_uuid))
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.purge(sample_action)

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)

    async def test_purge_vfolder_invalid_status_propagates(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_action: PurgeVFolderAction,
    ) -> None:
        """Test that VFolderFilterStatusFailed from repository is propagated."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(side_effect=VFolderFilterStatusFailed)

        with pytest.raises(VFolderFilterStatusFailed):
            await vfolder_service.purge(sample_action)

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)


class TestVFolderFileServiceCreateArchiveDownload:
    """Tests for VFolderFileService.create_archive_download_session() method."""

    STORAGE_URL = yarl.URL("https://storage.example.com")
    PROXY_NAME = "proxy1"
    VOLUME_NAME = "volume1"
    STORAGE_TOKEN = "test-jwt-token"
    SAMPLE_FILES = ["file1.txt", "dir1/file2.txt"]

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        manager = MagicMock()
        manager.get_proxy_and_volume.return_value = (self.PROXY_NAME, self.VOLUME_NAME)
        manager.get_client_api_url.return_value = self.STORAGE_URL
        mock_client = MagicMock()
        mock_client.create_archive_download_token = AsyncMock(
            return_value={"token": self.STORAGE_TOKEN}
        )
        manager.get_manager_facing_client.return_value = mock_client
        return manager

    @pytest.fixture
    def sample_validated_info(self, sample_vfolder_uuid: uuid.UUID) -> ValidatedVFolderInfo:
        return ValidatedVFolderInfo(
            vfolder_id=VFolderID(
                quota_scope_id=QuotaScopeID.parse(f"user:{sample_vfolder_uuid}"),
                folder_id=sample_vfolder_uuid,
            ),
            host="local:volume1",
            unmanaged_path=None,
        )

    @pytest.fixture
    def file_service(
        self,
        mock_config_provider: MagicMock,
        mock_storage_manager: MagicMock,
        sample_validated_info: ValidatedVFolderInfo,
    ) -> VFolderFileService:
        mock_vfolder_repo = MagicMock()
        mock_vfolder_repo.get_validated_vfolder_id = AsyncMock(return_value=sample_validated_info)
        return VFolderFileService(
            config_provider=mock_config_provider,
            storage_manager=mock_storage_manager,
            vfolder_repository=mock_vfolder_repo,
            user_repository=MagicMock(),
        )

    @pytest.fixture
    def sample_action(self, sample_vfolder_uuid: uuid.UUID) -> CreateArchiveDownloadSessionAction:
        return CreateArchiveDownloadSessionAction(
            keypair_resource_policy={"default": {}},
            vfolder_uuid=sample_vfolder_uuid,
            files=self.SAMPLE_FILES,
        )

    async def test_download_archive_success(
        self,
        file_service: VFolderFileService,
        sample_action: CreateArchiveDownloadSessionAction,
        sample_vfolder_uuid: uuid.UUID,
    ) -> None:
        """Test successful archive download session creation."""
        result = await file_service.create_archive_download_session(sample_action)

        assert isinstance(result, CreateArchiveDownloadSessionActionResult)
        assert result.token == self.STORAGE_TOKEN
        assert result.url == str(self.STORAGE_URL / "download-archive")
        assert result.vfolder_uuid == sample_vfolder_uuid

    async def test_download_archive_rejects_when_no_user_context(
        self,
        mock_config_provider: MagicMock,
        mock_storage_manager: MagicMock,
        sample_action: CreateArchiveDownloadSessionAction,
    ) -> None:
        """Test that AuthorizationFailed from repository is propagated."""
        mock_vfolder_repo = MagicMock()
        mock_vfolder_repo.get_validated_vfolder_id = AsyncMock(
            side_effect=AuthorizationFailed("User context is not available")
        )
        file_service = VFolderFileService(
            config_provider=mock_config_provider,
            storage_manager=mock_storage_manager,
            vfolder_repository=mock_vfolder_repo,
            user_repository=MagicMock(),
        )

        with pytest.raises(AuthorizationFailed):
            await file_service.create_archive_download_session(sample_action)

    async def test_download_archive_calls_storage_proxy_with_correct_params(
        self,
        file_service: VFolderFileService,
        mock_storage_manager: MagicMock,
        sample_action: CreateArchiveDownloadSessionAction,
    ) -> None:
        """Test that storage proxy client is called with correct parameters."""
        await file_service.create_archive_download_session(sample_action)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.create_archive_download_token.assert_called_once()
        call_kwargs = mock_client.create_archive_download_token.call_args.kwargs
        assert call_kwargs["volume"] == self.VOLUME_NAME
        assert call_kwargs["files"] == sample_action.files

    async def test_download_archive_passes_filename_to_storage_proxy(
        self,
        file_service: VFolderFileService,
        mock_storage_manager: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
    ) -> None:
        """Test that custom filename is forwarded to storage proxy client."""
        action_with_filename = CreateArchiveDownloadSessionAction(
            keypair_resource_policy={"default": {}},
            vfolder_uuid=sample_vfolder_uuid,
            files=self.SAMPLE_FILES,
            filename="my-export.zip",
        )
        await file_service.create_archive_download_session(action_with_filename)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        call_kwargs = mock_client.create_archive_download_token.call_args.kwargs
        assert call_kwargs["filename"] == "my-export.zip"

    async def test_download_archive_passes_none_filename_when_omitted(
        self,
        file_service: VFolderFileService,
        mock_storage_manager: MagicMock,
        sample_action: CreateArchiveDownloadSessionAction,
    ) -> None:
        """Test that filename=None is passed when not specified in action."""
        await file_service.create_archive_download_session(sample_action)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        call_kwargs = mock_client.create_archive_download_token.call_args.kwargs
        assert call_kwargs["filename"] is None


@dataclass(frozen=True)
class CloneUsageModeCase:
    source: VFolderUsageMode
    request: VFolderUsageMode | None
    expected: VFolderUsageMode


class TestVFolderServiceCloneUsageModeInheritance:
    """Regression tests for BA-5527: clone should inherit source vfolder's usage_mode."""

    @pytest.fixture
    def user_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def source_vfolder_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def target_vfolder_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def bgtask_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def source_vfolder_data(self, source_vfolder_uuid: uuid.UUID) -> VFolderData:
        return VFolderData(
            id=source_vfolder_uuid,
            name="source-vfolder",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID.parse(f"user:{source_vfolder_uuid}"),
            usage_mode=VFolderUsageMode.MODEL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            last_used=None,
            creator="test@example.com",
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=source_vfolder_uuid,
            group=None,
            cloneable=True,
            status=VFolderOperationStatus.READY,
        )

    @pytest.fixture
    def mock_repo(
        self,
        target_vfolder_uuid: uuid.UUID,
        bgtask_id: uuid.UUID,
        source_vfolder_data: VFolderData,
    ) -> MagicMock:
        repo = MagicMock(spec=VfolderRepository)
        repo.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        repo.check_vfolder_name_exists = AsyncMock(return_value=False)
        repo.get_allowed_vfolder_hosts = AsyncMock(return_value={})
        repo.ensure_host_permission_allowed = AsyncMock()
        repo.get_max_vfolder_count = AsyncMock(return_value=0)
        repo.get_user_email_by_id = AsyncMock(return_value="test@example.com")
        repo.initiate_vfolder_clone = AsyncMock(return_value=(bgtask_id, target_vfolder_uuid))
        repo.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=source_vfolder_data,
                        is_owner=True,
                        effective_permission=VFolderMountPermission.READ_WRITE,
                    ),
                ],
            )
        )
        return repo

    @pytest.fixture
    def mock_service(
        self,
        mock_repo: MagicMock,
        mock_config_provider: MagicMock,
    ) -> VFolderService:
        return VFolderService(
            config_provider=mock_config_provider,
            etcd=MagicMock(),
            storage_manager=MagicMock(),
            background_task_manager=MagicMock(),
            vfolder_repository=mock_repo,
            user_repository=MagicMock(),
            valkey_stat_client=MagicMock(),
        )

    @pytest.mark.parametrize(
        "case",
        [
            # None → inherit from source
            CloneUsageModeCase(VFolderUsageMode.MODEL, None, VFolderUsageMode.MODEL),
            CloneUsageModeCase(VFolderUsageMode.GENERAL, None, VFolderUsageMode.GENERAL),
            CloneUsageModeCase(VFolderUsageMode.DATA, None, VFolderUsageMode.DATA),
            # explicit → override source
            CloneUsageModeCase(
                VFolderUsageMode.MODEL, VFolderUsageMode.GENERAL, VFolderUsageMode.GENERAL
            ),
        ],
    )
    async def test_clone_usage_mode_resolution(
        self,
        mock_service: VFolderService,
        mock_repo: MagicMock,
        user_uuid: uuid.UUID,
        source_vfolder_uuid: uuid.UUID,
        source_vfolder_data: VFolderData,
        case: CloneUsageModeCase,
    ) -> None:
        """Clone should inherit source usage_mode when None, or use explicit value."""
        source_vfolder_data.usage_mode = case.source

        action = CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=source_vfolder_uuid,
            target_name="cloned-vfolder",
            target_host="local:volume1",
            target_quota_scope_id=None,
            cloneable=False,
            usage_mode=case.request,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        result = await mock_service.clone(action)

        assert isinstance(result, CloneVFolderActionResult)
        assert result.usage_mode == case.expected
        clone_info = mock_repo.initiate_vfolder_clone.call_args[0][0]
        assert clone_info.usage_mode == case.expected
