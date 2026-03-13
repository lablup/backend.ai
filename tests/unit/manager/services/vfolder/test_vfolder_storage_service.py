"""
Unit tests for VFolderService storage management operations.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import msgpack
import pytest

from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.errors.storage import (
    VFolderBadRequest,
    VFolderOperationFailed,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    ChangeVFolderOwnershipActionResult,
    GetQuotaAction,
    GetQuotaActionResult,
    ListAllHostsAction,
    ListAllHostsActionResult,
    ListHostsAction,
    ListHostsActionResult,
    MountHostAction,
    MountHostActionResult,
    UmountHostAction,
    UmountHostActionResult,
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


@pytest.fixture
def user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def vfolder_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_vfolder_repository() -> MagicMock:
    return MagicMock(spec=VfolderRepository)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
    provider.legacy_etcd_config_loader.get_raw = AsyncMock(return_value="/mnt")
    provider.config.volumes.default_host = "proxy1:volume1"
    provider.config.watcher.token = "test-token"
    return provider


@pytest.fixture
def mock_storage_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_proxy_and_volume.return_value = ("proxy1", "volume1")
    manager._exposed_volume_info = ["percentage", "used_bytes", "capacity_bytes"]
    mock_client = MagicMock()
    mock_client.get_volume_quota = AsyncMock(return_value={"quota_bytes": 1073741824})
    mock_client.update_volume_quota = AsyncMock()
    mock_client.get_fs_usage = AsyncMock(
        return_value={"used_bytes": 500000, "capacity_bytes": 1000000}
    )
    manager.get_manager_facing_client.return_value = mock_client
    manager.get_all_volumes = AsyncMock(
        return_value=[
            (
                "proxy1",
                {
                    "name": "volume1",
                    "backend": "xfs",
                    "capabilities": ["quota"],
                    "path": "/mnt/volume1",
                },
            ),
            (
                "proxy2",
                {
                    "name": "volume2",
                    "backend": "ceph",
                    "capabilities": ["quota", "snapshot"],
                    "path": "/mnt/volume2",
                },
            ),
        ]
    )
    manager.get_sftp_scaling_groups = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_etcd() -> MagicMock:
    etcd = MagicMock()
    etcd.get = AsyncMock(return_value=None)
    return etcd


@pytest.fixture
def mock_valkey_stat_client() -> MagicMock:
    client = MagicMock()
    client.get_volume_usage = AsyncMock(return_value=None)
    return client


@pytest.fixture
def vfolder_service(
    mock_config_provider: MagicMock,
    mock_storage_manager: MagicMock,
    mock_vfolder_repository: MagicMock,
    mock_etcd: MagicMock,
    mock_valkey_stat_client: MagicMock,
) -> VFolderService:
    return VFolderService(
        config_provider=mock_config_provider,
        etcd=mock_etcd,
        storage_manager=mock_storage_manager,
        background_task_manager=MagicMock(),
        vfolder_repository=mock_vfolder_repository,
        user_repository=MagicMock(),
        valkey_stat_client=mock_valkey_stat_client,
    )


class TestListAllHostsAction:
    async def test_enumerates_all_proxies_volumes(
        self,
        vfolder_service: VFolderService,
        mock_storage_manager: MagicMock,
    ) -> None:
        action = ListAllHostsAction()
        result = await vfolder_service.list_all_hosts(action)

        assert isinstance(result, ListAllHostsActionResult)
        assert "proxy1:volume1" in result.allowed
        assert "proxy2:volume2" in result.allowed
        assert len(result.allowed) == 2
        mock_storage_manager.get_all_volumes.assert_awaited_once()

    async def test_sets_and_returns_default_host(
        self,
        vfolder_service: VFolderService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.config.volumes.default_host = "proxy1:volume1"
        action = ListAllHostsAction()
        result = await vfolder_service.list_all_hosts(action)

        assert result.default == "proxy1:volume1"

    async def test_default_host_not_in_volumes_returns_none(
        self,
        vfolder_service: VFolderService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.config.volumes.default_host = "nonexistent:host"
        action = ListAllHostsAction()
        result = await vfolder_service.list_all_hosts(action)

        assert result.default is None


class TestListHostsAction:
    async def test_filters_by_user_resource_policy(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_allowed_hosts_for_listing = AsyncMock(
            return_value=VFolderHostPermissionMap({
                "proxy1:volume1": {VFolderHostPermission.CREATE, VFolderHostPermission.MODIFY},
            })
        )
        action = ListHostsAction(
            user_uuid=user_uuid,
            domain_name="default",
            group_id=None,
            resource_policy={"max_vfolder_count": 10},
        )
        result = await vfolder_service.list_hosts(action)

        assert isinstance(result, ListHostsActionResult)
        assert "proxy1:volume1" in result.allowed
        assert "proxy2:volume2" not in result.allowed
        mock_vfolder_repository.get_allowed_hosts_for_listing.assert_awaited_once()

    async def test_volume_info_includes_backend_capabilities_usage(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_allowed_hosts_for_listing = AsyncMock(
            return_value=VFolderHostPermissionMap({
                "proxy1:volume1": {VFolderHostPermission.CREATE},
            })
        )
        action = ListHostsAction(
            user_uuid=user_uuid,
            domain_name="default",
            group_id=None,
            resource_policy={},
        )
        result = await vfolder_service.list_hosts(action)

        vol_info = result.volume_info["proxy1:volume1"]
        assert vol_info["backend"] == "xfs"
        assert vol_info["capabilities"] == ["quota"]
        assert "usage" in vol_info

    async def test_valkey_cache_hit_returns_cached_usage(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_valkey_stat_client: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        cached_data = msgpack.packb({"used": 100, "total": 200, "percentage": 0.5})
        mock_valkey_stat_client.get_volume_usage = AsyncMock(return_value=cached_data)

        mock_vfolder_repository.get_allowed_hosts_for_listing = AsyncMock(
            return_value=VFolderHostPermissionMap({
                "proxy1:volume1": {VFolderHostPermission.CREATE},
            })
        )
        action = ListHostsAction(
            user_uuid=user_uuid,
            domain_name="default",
            group_id=None,
            resource_policy={},
        )
        result = await vfolder_service.list_hosts(action)

        vol_info = result.volume_info["proxy1:volume1"]
        assert vol_info["usage"]["used"] == 100
        assert vol_info["usage"]["total"] == 200
        mock_storage_manager.get_manager_facing_client.return_value.get_fs_usage.assert_not_awaited()

    async def test_valkey_cache_miss_fetches_from_storage(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_valkey_stat_client: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_valkey_stat_client.get_volume_usage = AsyncMock(return_value=None)

        mock_vfolder_repository.get_allowed_hosts_for_listing = AsyncMock(
            return_value=VFolderHostPermissionMap({
                "proxy1:volume1": {VFolderHostPermission.CREATE},
            })
        )
        action = ListHostsAction(
            user_uuid=user_uuid,
            domain_name="default",
            group_id=None,
            resource_policy={},
        )
        result = await vfolder_service.list_hosts(action)

        vol_info = result.volume_info["proxy1:volume1"]
        assert "usage" in vol_info
        mock_storage_manager.get_manager_facing_client.return_value.get_fs_usage.assert_awaited_once()


class TestGetQuotaAction:
    async def test_owner_returns_quota_bytes(
        self,
        vfolder_service: VFolderService,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        action = GetQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.SUPERADMIN,
            user_uuid=user_uuid,
            domain_name="default",
        )
        result = await vfolder_service.get_quota(action)

        assert isinstance(result, GetQuotaActionResult)
        assert result.data["quota_bytes"] == 1073741824

    async def test_non_admin_checks_accessibility(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.check_vfolder_accessible = AsyncMock()
        action = GetQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.USER,
            user_uuid=user_uuid,
            domain_name="default",
        )
        await vfolder_service.get_quota(action)

        mock_vfolder_repository.check_vfolder_accessible.assert_awaited_once_with(
            vfolder_id=vfolder_uuid,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            allowed_vfolder_types=["user", "group"],
        )

    async def test_superadmin_skips_accessibility_check(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.check_vfolder_accessible = AsyncMock()
        action = GetQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.SUPERADMIN,
            user_uuid=user_uuid,
            domain_name="default",
        )
        await vfolder_service.get_quota(action)

        mock_vfolder_repository.check_vfolder_accessible.assert_not_awaited()


class TestUpdateQuotaAction:
    async def test_update_within_resource_policy_max(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.update_vfolder_max_size = AsyncMock()
        action = UpdateQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.SUPERADMIN,
            user_uuid=user_uuid,
            domain_name="default",
            resource_policy={"max_quota_scope_size": 2147483648},
            size_bytes=1073741824,
        )
        result = await vfolder_service.update_quota(action)

        assert isinstance(result, UpdateQuotaActionResult)
        assert result.size_bytes == 1073741824

    async def test_exceeding_max_caps_to_max_quota_scope_size(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.update_vfolder_max_size = AsyncMock()
        max_quota = 1073741824
        action = UpdateQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.SUPERADMIN,
            user_uuid=user_uuid,
            domain_name="default",
            resource_policy={"max_quota_scope_size": max_quota},
            size_bytes=max_quota * 2,
        )
        result = await vfolder_service.update_quota(action)

        assert result.size_bytes == max_quota
        mock_storage_manager.get_manager_facing_client.return_value.update_volume_quota.assert_awaited_once()

    async def test_passes_size_to_storage_proxy_and_updates_db(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        vfolder_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.update_vfolder_max_size = AsyncMock()
        quota_bytes = 1048576
        action = UpdateQuotaAction(
            folder_host="proxy1:volume1",
            vfid="vfid-123",
            vfolder_id=vfolder_uuid,
            unmanaged_path=None,
            user_role=UserRole.SUPERADMIN,
            user_uuid=user_uuid,
            domain_name="default",
            resource_policy={},
            size_bytes=quota_bytes,
        )
        await vfolder_service.update_quota(action)

        mock_storage_manager.get_manager_facing_client.return_value.update_volume_quota.assert_awaited_once_with(
            "volume1", "vfid-123", quota_bytes
        )
        mock_vfolder_repository.update_vfolder_max_size.assert_awaited_once_with(
            vfolder_uuid,
            1,  # ceil(1048576 / 2**20) = 1
        )


class TestChangeVFolderOwnershipAction:
    async def test_ownership_transfer_to_another_user(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.change_vfolder_ownership = AsyncMock()
        action = ChangeVFolderOwnershipAction(
            vfolder_id=vfolder_uuid,
            user_email="new-owner@example.com",
        )
        result = await vfolder_service.change_vfolder_ownership(action)

        assert isinstance(result, ChangeVFolderOwnershipActionResult)
        mock_vfolder_repository.change_vfolder_ownership.assert_awaited_once_with(
            vfolder_uuid, "new-owner@example.com"
        )

    async def test_non_existent_email_raises_error(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.change_vfolder_ownership = AsyncMock(
            side_effect=UserNotFound("User not found")
        )
        action = ChangeVFolderOwnershipAction(
            vfolder_id=vfolder_uuid,
            user_email="nonexistent@example.com",
        )
        with pytest.raises(UserNotFound):
            await vfolder_service.change_vfolder_ownership(action)


class TestMountHostAction:
    async def test_sends_mount_to_agents(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_etcd: MagicMock,
    ) -> None:
        mock_vfolder_repository.get_alive_agent_ids = AsyncMock(return_value=[])
        action = MountHostAction(
            name="test-volume",
            fs_location="/dev/sda1",
            fs_type="ext4",
            options=None,
            scaling_group=None,
            fstab_path=None,
            edit_fstab=False,
        )
        result = await vfolder_service.mount_host(action)

        assert isinstance(result, MountHostActionResult)
        assert result.manager.success is True
        mock_vfolder_repository.get_alive_agent_ids.assert_awaited_once_with(None)

    async def test_specific_scaling_group_filtering(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        mock_vfolder_repository.get_alive_agent_ids = AsyncMock(return_value=[])
        action = MountHostAction(
            name="test-volume",
            fs_location="/dev/sda1",
            scaling_group="sg-01",
        )
        await vfolder_service.mount_host(action)

        mock_vfolder_repository.get_alive_agent_ids.assert_awaited_once_with("sg-01")


class TestUmountHostAction:
    async def test_active_session_using_volume_raises_error(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_vfolder_repository.get_active_kernel_mount_names = AsyncMock(
            return_value=["test-volume"]
        )
        action = UmountHostAction(
            name="test-volume",
        )
        with pytest.raises(VFolderOperationFailed, match="Target host is used in sessions"):
            await vfolder_service.umount_host(action)

    async def test_mountpoint_equals_mount_prefix_raises_bad_request(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_raw = AsyncMock(return_value="/mnt")
        action = UmountHostAction(
            name=".",
        )
        with pytest.raises(
            VFolderBadRequest, match="Mount prefix and mountpoint cannot be the same"
        ):
            await vfolder_service.umount_host(action)

    async def test_successful_umount_returns_result(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
    ) -> None:
        mock_vfolder_repository.get_active_kernel_mount_names = AsyncMock(return_value=[])
        mock_vfolder_repository.get_alive_agent_ids = AsyncMock(return_value=[])
        action = UmountHostAction(
            name="test-volume",
        )
        result = await vfolder_service.umount_host(action)

        assert isinstance(result, UmountHostActionResult)
        assert result.manager.success is True
