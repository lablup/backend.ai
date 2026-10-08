"""
Tests for VFolderService and VFolderFileService functionality.
"""

from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import QuotaScopeID, VFolderID, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    ValidatedVFolderInfo,
    VFolderData,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderUsageData,
)
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.storage import (
    VFolderFilterStatusFailed,
    VFolderNotFound,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.base import (
    PurgeVFolderAction,
    PurgeVFolderActionResult,
)
from ai.backend.manager.services.vfolder.actions.bulk_load_mount_levels import (
    BulkLoadVFolderMountLevelsAction,
)
from ai.backend.manager.services.vfolder.actions.file import (
    CreateArchiveDownloadSessionAction,
    CreateArchiveDownloadSessionActionResult,
)
from ai.backend.manager.services.vfolder.actions.get_usage import (
    GetVFolderUsageAction,
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
        id=VFolderUUID(sample_vfolder_uuid),
        name="test-vfolder",
        host="local:volume1",
        domain_name="default",
        quota_scope_id=QuotaScopeID.parse(f"user:{sample_vfolder_uuid}"),
        usage_mode=VFolderUsageMode.GENERAL,
        default_mount_permission=VFolderMountPolicy.READ_WRITE,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        last_used=None,
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        creator="test@example.com",
        creator_id=sample_vfolder_uuid,
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
            own_check=MagicMock(),
        )

    @pytest.fixture
    def sample_action(self, sample_vfolder_uuid: uuid.UUID) -> PurgeVFolderAction:
        return PurgeVFolderAction(vfolder_uuid=VFolderUUID(sample_vfolder_uuid))

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
        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.vfolder_uuid)

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

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.vfolder_uuid)

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

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.vfolder_uuid)


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
            vfolder_uuid=VFolderUUID(sample_vfolder_uuid),
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
            vfolder_uuid=VFolderUUID(sample_vfolder_uuid),
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


class TestVFolderServiceGetFolderUsage:
    """Tests for VFolderService.get_folder_usage().

    Verifies the contract: measurements come live from the storage proxy,
    quota limits come from the vfolder row, and unmanaged vfolders skip
    the storage proxy entirely.
    """

    @pytest.fixture
    def mock_storage_client(self) -> MagicMock:
        client = MagicMock()
        client.get_folder_usage = AsyncMock(return_value={"file_count": 2, "used_bytes": 524308})
        return client

    @pytest.fixture
    def mock_storage_manager(self, mock_storage_client: MagicMock) -> MagicMock:
        manager = MagicMock()
        manager.get_proxy_and_volume = MagicMock(return_value=("local", "volume1"))
        manager.get_manager_facing_client = MagicMock(return_value=mock_storage_client)
        return manager

    @pytest.fixture
    def vfolder_service(
        self,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> VFolderService:
        return VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=mock_storage_manager,
            background_task_manager=MagicMock(),
            vfolder_repository=mock_vfolder_repository,
            user_repository=MagicMock(),
            valkey_stat_client=MagicMock(),
            own_check=MagicMock(),
        )

    @pytest.fixture
    def sample_action(self, sample_vfolder_uuid: uuid.UUID) -> GetVFolderUsageAction:
        return GetVFolderUsageAction(vfolder_uuid=VFolderUUID(sample_vfolder_uuid))

    async def test_managed_vfolder_returns_storage_proxy_measurements(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_vfolder_data: VFolderData,
        sample_action: GetVFolderUsageAction,
    ) -> None:
        """num_files/used_bytes come straight from the storage proxy reply."""
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=sample_vfolder_data)

        result = await vfolder_service.get_folder_usage(sample_action)

        assert result.vfolder_uuid == sample_vfolder_uuid
        assert result.usage == VFolderUsageData(
            num_files=2,
            used_bytes=524308,
        )

    async def test_storage_proxy_receives_canonical_vfid(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_client: MagicMock,
        sample_vfolder_data: VFolderData,
        sample_action: GetVFolderUsageAction,
    ) -> None:
        """The vfid must use the canonical VFolderID serialization
        (quota scope prefix + dash-less folder hex)."""
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=sample_vfolder_data)

        await vfolder_service.get_folder_usage(sample_action)

        expected_vfid = str(VFolderID(sample_vfolder_data.quota_scope_id, sample_vfolder_data.id))
        mock_storage_client.get_folder_usage.assert_awaited_once_with("volume1", expected_vfid)

    async def test_unmanaged_vfolder_returns_none_without_storage_call(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_vfolder_data: VFolderData,
        sample_action: GetVFolderUsageAction,
    ) -> None:
        """Unmanaged vfolders have no storage-proxy backing: usage is None and
        no storage client is consulted."""
        unmanaged_data = dataclasses.replace(sample_vfolder_data, unmanaged_path="/mnt/external")
        mock_vfolder_repository.get_by_id = AsyncMock(return_value=unmanaged_data)

        result = await vfolder_service.get_folder_usage(sample_action)

        assert result.vfolder_uuid == sample_vfolder_uuid
        assert result.usage is None
        mock_storage_manager.get_manager_facing_client.assert_not_called()


class TestVFolderServiceBulkLoadMountLevels:
    """The mount level the caller gets on each folder named."""

    @pytest.fixture
    def caller_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def as_caller(self, caller_id: uuid.UUID) -> Iterator[None]:
        with with_user(
            UserData(
                user_id=caller_id,
                is_authorized=True,
                is_admin=False,
                is_superadmin=False,
                role=UserRole.USER,
                domain_name="default",
                domain_id=DomainID(uuid.uuid4()),
            )
        ):
            yield

    @pytest.fixture
    def own_check(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def vfolder_service(
        self, mock_vfolder_repository: MagicMock, own_check: MagicMock
    ) -> VFolderService:
        return VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=MagicMock(),
            background_task_manager=MagicMock(),
            vfolder_repository=mock_vfolder_repository,
            user_repository=MagicMock(),
            valkey_stat_client=MagicMock(),
            own_check=own_check,
        )

    async def _level_of(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        own_check: MagicMock,
        folder: VFolderData,
        *,
        held: Permission = Permission.READ,
        user_policy: VFolderMountPolicy | None = None,
    ) -> VFolderMountPolicy | None:
        own_check.held = AsyncMock(return_value={folder.id: held})
        mock_vfolder_repository.batch_load_by_ids = AsyncMock(return_value=[folder])
        mock_vfolder_repository.user_mount_policies_of = AsyncMock(
            return_value={} if user_policy is None else {folder.id: user_policy}
        )
        result = await vfolder_service.bulk_load_mount_levels(
            BulkLoadVFolderMountLevelsAction(vfolder_ids=[folder.id])
        )
        return result.values().get(folder.id)

    @pytest.mark.usefixtures("as_caller")
    async def test_the_owner_of_a_personal_folder_gets_read_write(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        own_check: MagicMock,
        sample_vfolder_data: VFolderData,
        caller_id: uuid.UUID,
    ) -> None:
        folder = dataclasses.replace(
            sample_vfolder_data,
            user=caller_id,
            default_mount_permission=VFolderMountPolicy.NONE,
        )

        level = await self._level_of(
            vfolder_service, mock_vfolder_repository, own_check, folder, held=Permission.full()
        )

        assert level == VFolderMountPolicy.READ_WRITE

    @pytest.mark.usefixtures("as_caller")
    async def test_a_recipient_gets_their_policy_row(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        own_check: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        folder = dataclasses.replace(
            sample_vfolder_data, default_mount_permission=VFolderMountPolicy.NONE
        )

        level = await self._level_of(
            vfolder_service,
            mock_vfolder_repository,
            own_check,
            folder,
            user_policy=VFolderMountPolicy.READ_ONLY,
        )

        assert level == VFolderMountPolicy.READ_ONLY

    @pytest.mark.usefixtures("as_caller")
    async def test_read_access_without_a_row_gets_the_folder_default(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        own_check: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        folder = dataclasses.replace(
            sample_vfolder_data, default_mount_permission=VFolderMountPolicy.NONE
        )

        level = await self._level_of(vfolder_service, mock_vfolder_repository, own_check, folder)

        assert level == VFolderMountPolicy.NONE

    @pytest.mark.usefixtures("as_caller")
    async def test_a_project_folder_without_a_row_gets_its_read_only_default(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        own_check: MagicMock,
        sample_vfolder_data: VFolderData,
    ) -> None:
        folder = dataclasses.replace(
            sample_vfolder_data,
            ownership_type=VFolderOwnershipType.GROUP,
            user=None,
            group=uuid.uuid4(),
            usage_mode=VFolderUsageMode.MODEL,
            default_mount_permission=VFolderMountPolicy.READ_ONLY,
        )

        level = await self._level_of(vfolder_service, mock_vfolder_repository, own_check, folder)

        assert level == VFolderMountPolicy.READ_ONLY
