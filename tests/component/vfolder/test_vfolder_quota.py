from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.vfolder import (
    GetQuotaQuery,
    GetQuotaResponse,
    GetUsageQuery,
    GetUsageResponse,
    GetUsedBytesQuery,
    GetUsedBytesResponse,
    UpdateQuotaReq,
    UpdateQuotaResponse,
)
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


@pytest.fixture()
def storage_manager() -> StorageSessionManager:
    """Mock StorageSessionManager with configured storage proxy client methods.

    Overrides the parent conftest mock so that quota and usage endpoints work
    without a live storage-proxy connection.
    """
    mock = MagicMock(spec=StorageSessionManager)
    mock_client = AsyncMock()
    mock_client.get_volume_quota.return_value = {"used_bytes": 0, "limit_bytes": 0}
    mock_client.update_volume_quota.return_value = None
    mock_client.get_folder_usage.return_value = {"used_bytes": 0, "file_count": 0}
    mock_client.get_used_bytes.return_value = {"used_bytes": 0}
    mock.get_proxy_and_volume.return_value = ("local", "volume")
    mock.get_manager_facing_client.return_value = mock_client
    return mock


class TestStorageQuotaScope:
    """Storage quota CRUD and access control via the quota scope API.
    Storage-proxy calls are mocked via the storage_manager fixture in conftest."""

    async def test_get_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Scenario: Admin queries the quota for an existing USER vfolder on the
        'local' storage host. Verifies the response is a GetQuotaResponse with
        a data dict containing quota limit information."""
        result = await admin_registry.vfolder.get_quota(
            GetQuotaQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetQuotaResponse)
        assert isinstance(result.data, dict)

    async def test_update_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Scenario: Admin updates the quota for an existing vfolder to 100 MiB.
        Verifies the response is an UpdateQuotaResponse, confirming the
        storage-proxy accepted the new quota limit."""
        result = await admin_registry.vfolder.update_quota(
            UpdateQuotaReq(
                folder_host="local",
                id=target_vfolder["id"],
                input={"size_bytes": 1024 * 1024 * 100},
            ),
        )
        assert isinstance(result, UpdateQuotaResponse)

    async def test_get_usage(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Scenario: Admin queries folder usage (file_count, used_bytes) for an
        existing vfolder. Verifies the response is a GetUsageResponse with a
        data dict containing usage statistics from the storage-proxy."""
        result = await admin_registry.vfolder.get_usage(
            GetUsageQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetUsageResponse)
        assert isinstance(result.data, dict)

    async def test_get_used_bytes(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Scenario: Admin queries the used_bytes metric for an existing vfolder.
        This is a lightweight alternative to get_usage that returns only the byte
        count. Verifies the response is a GetUsedBytesResponse with a data dict."""
        result = await admin_registry.vfolder.get_used_bytes(
            GetUsedBytesQuery(
                folder_host="local",
                id=target_vfolder["id"],
            ),
        )
        assert isinstance(result, GetUsedBytesResponse)
        assert isinstance(result.data, dict)

    async def test_regular_user_can_get_own_quota(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """Scenario: A regular (non-admin) user creates a vfolder under their own
        quota scope (QuotaScopeType.USER) and queries its quota. Verifies that
        non-admin users are allowed to read quota info for their own vfolders."""
        user_uuid = regular_user_fixture.user_uuid
        vf = await vfolder_factory(
            user=str(user_uuid),
            creator="user-test@test.local",
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
        )
        result = await user_registry.vfolder.get_quota(
            GetQuotaQuery(folder_host="local", id=vf["id"]),
        )
        assert isinstance(result, GetQuotaResponse)

    async def test_regular_user_cannot_update_others_quota(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Scenario: A regular user attempts to update the quota of a vfolder owned
        by the admin. The server should reject this with BackendAPIError because
        quota modification requires admin privileges or ownership of the vfolder."""
        with pytest.raises(BackendAPIError):
            await user_registry.vfolder.update_quota(
                UpdateQuotaReq(
                    folder_host="local",
                    id=target_vfolder["id"],
                    input={"size_bytes": 999999},
                ),
            )
