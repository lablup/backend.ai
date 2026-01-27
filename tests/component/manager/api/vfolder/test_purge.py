from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

# Explicitly import to ensure Pants includes this module in the test build
import ai.backend.manager.api.vfolder  # noqa: F401
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.vfolder import VFolderOperationStatus, VFolderRow
from ai.backend.manager.server import (
    database_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    repositories_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.vfolder.actions.base import (
    PurgeVFolderAction,
    PurgeVFolderActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService

# Admin user UUID from example-users.json (role: superadmin)
ADMIN_USER_UUID = "f38dea23-50fa-42a0-b5ae-338f5f4693f4"

# VFolder IDs for test fixtures
VFOLDER_DELETE_PENDING_ID = "00000000-0000-0000-0000-000000000001"
VFOLDER_DELETE_COMPLETE_ID = "00000000-0000-0000-0000-000000000002"
VFOLDER_READY_ID = "00000000-0000-0000-0000-000000000003"
VFOLDER_MOUNTED_ID = "00000000-0000-0000-0000-000000000004"
VFOLDER_PERFORMING_ID = "00000000-0000-0000-0000-000000000005"
VFOLDER_CLONING_ID = "00000000-0000-0000-0000-000000000006"
VFOLDER_DELETE_ONGOING_ID = "00000000-0000-0000-0000-000000000007"
VFOLDER_DELETE_ERROR_ID = "00000000-0000-0000-0000-000000000008"


def _create_vfolder_fixture(
    vfolder_id: str,
    name: str,
    status: VFolderOperationStatus,
) -> dict[str, Any]:
    """Create a vfolder fixture dictionary."""
    return {
        "id": vfolder_id,
        "host": "local:volume1",
        "domain_name": "default",
        "name": name,
        "quota_scope_id": f"user:{ADMIN_USER_UUID}",
        "usage_mode": "general",
        "permission": "rw",
        "ownership_type": "user",
        "status": status,
        "cloneable": False,
        "max_files": 0,
        "num_files": 0,
        "user": ADMIN_USER_UUID,
        "group": None,
    }


FIXTURES_FOR_PURGE_VFOLDER_TEST = [
    {
        "vfolders": [
            _create_vfolder_fixture(
                VFOLDER_DELETE_PENDING_ID,
                "vfolder_delete_pending",
                VFolderOperationStatus.DELETE_PENDING,
            ),
            _create_vfolder_fixture(
                VFOLDER_DELETE_COMPLETE_ID,
                "vfolder_delete_complete",
                VFolderOperationStatus.DELETE_COMPLETE,
            ),
            _create_vfolder_fixture(
                VFOLDER_READY_ID,
                "vfolder_ready",
                VFolderOperationStatus.READY,
            ),
            _create_vfolder_fixture(
                VFOLDER_MOUNTED_ID,
                "vfolder_mounted",
                VFolderOperationStatus.MOUNTED,
            ),
            _create_vfolder_fixture(
                VFOLDER_PERFORMING_ID,
                "vfolder_performing",
                VFolderOperationStatus.PERFORMING,
            ),
            _create_vfolder_fixture(
                VFOLDER_CLONING_ID,
                "vfolder_cloning",
                VFolderOperationStatus.CLONING,
            ),
            _create_vfolder_fixture(
                VFOLDER_DELETE_ONGOING_ID,
                "vfolder_delete_ongoing",
                VFolderOperationStatus.DELETE_ONGOING,
            ),
            _create_vfolder_fixture(
                VFOLDER_DELETE_ERROR_ID,
                "vfolder_delete_error",
                VFolderOperationStatus.DELETE_ERROR,
            ),
        ],
    },
]


@asynccontextmanager
async def mock_processors_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """
    Mock processors context that provides vfolder.purge_vfolder processor.

    This uses the real VFolderService to ensure the service layer logic is tested.
    Only the processor wrapper is mocked; the service layer executes real business logic.
    """
    # Create real VFolderService with actual dependencies
    # background_task_manager is mocked since purge() doesn't use it
    vfolder_service = VFolderService(
        config_provider=root_ctx.config_provider,
        storage_manager=root_ctx.storage_manager,
        background_task_manager=MagicMock(),  # Not used by purge()
        vfolder_repository=root_ctx.repositories.vfolder.repository,
        user_repository=root_ctx.repositories.user.repository,
    )

    async def mock_purge_vfolder(action: PurgeVFolderAction) -> PurgeVFolderActionResult:
        """Call real VFolderService.purge() method."""
        return await vfolder_service.purge(action)

    # Create mock processors structure that delegates to real service
    mock_processors = MagicMock()
    mock_vfolder_processor = MagicMock()
    mock_purge = MagicMock()
    mock_purge.wait_for_complete = AsyncMock(side_effect=mock_purge_vfolder)
    mock_vfolder_processor.purge_vfolder = mock_purge
    mock_processors.vfolder = mock_vfolder_processor
    root_ctx.processors = mock_processors
    yield


class TestPurgeVFolderAPI:
    """Tests for POST /folders/purge endpoint."""

    async def _verify_vfolder_deleted(self, app: Any, vfolder_id: str) -> None:
        """Verify vfolder is actually deleted from DB."""
        root_ctx = app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as session:
            query = sa.select(VFolderRow.id).where(VFolderRow.id == uuid.UUID(vfolder_id))
            result = await session.execute(query)
            row = result.scalar_one_or_none()
            assert row is None, f"VFolder {vfolder_id} should be deleted"

    async def _verify_vfolder_exists(self, app: Any, vfolder_id: str) -> None:
        """Verify vfolder still exists in DB."""
        root_ctx = app["_root.context"]
        async with root_ctx.db.begin_readonly_session() as session:
            query = sa.select(VFolderRow.id).where(VFolderRow.id == uuid.UUID(vfolder_id))
            result = await session.execute(query)
            row = result.scalar_one_or_none()
            assert row is not None, f"VFolder {vfolder_id} should still exist"

    # @pytest.mark.asyncio
    @pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_PURGE_VFOLDER_TEST, indirect=True)
    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "vfolder_id": VFOLDER_DELETE_PENDING_ID,
                "expected_status": HTTPStatus.NO_CONTENT,
            },
            {
                "vfolder_id": VFOLDER_DELETE_COMPLETE_ID,
                "expected_status": HTTPStatus.NO_CONTENT,
            },
        ],
        ids=["purge_delete_pending_vfolder", "purge_delete_complete_vfolder"],
    )
    async def test_purge_vfolder_success(
        self,
        test_case: dict[str, Any],
        etcd_fixture: None,
        mock_etcd_ctx: Any,
        mock_config_provider_ctx: Any,
        database_fixture: None,
        create_app_and_client: Any,
        get_headers: Any,
    ) -> None:
        """Test successful purge of PURGABLE vfolders."""
        app, client = await create_app_and_client(
            [
                mock_etcd_ctx,
                mock_config_provider_ctx,
                redis_ctx,
                database_ctx,
                storage_manager_ctx,
                repositories_ctx,
                monitoring_ctx,
                hook_plugin_ctx,
                mock_processors_ctx,
            ],
            [".vfolder", ".auth"],
        )

        url = "/folders/purge"
        params = {"vfolder_id": test_case["vfolder_id"]}
        req_bytes = json.dumps(params).encode()
        headers = get_headers("POST", url, req_bytes)

        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == test_case["expected_status"]

        # Verify deletion from database
        await self._verify_vfolder_deleted(app, test_case["vfolder_id"])

    # @pytest.mark.asyncio
    @pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_PURGE_VFOLDER_TEST, indirect=True)
    @pytest.mark.parametrize(
        "test_case",
        [
            {"vfolder_id": VFOLDER_READY_ID, "status": "READY"},
            {"vfolder_id": VFOLDER_MOUNTED_ID, "status": "MOUNTED"},
            {"vfolder_id": VFOLDER_PERFORMING_ID, "status": "PERFORMING"},
            {"vfolder_id": VFOLDER_CLONING_ID, "status": "CLONING"},
            {"vfolder_id": VFOLDER_DELETE_ONGOING_ID, "status": "DELETE_ONGOING"},
            {"vfolder_id": VFOLDER_DELETE_ERROR_ID, "status": "DELETE_ERROR"},
        ],
        ids=[
            "purge_ready_vfolder_fails",
            "purge_mounted_vfolder_fails",
            "purge_performing_vfolder_fails",
            "purge_cloning_vfolder_fails",
            "purge_delete_ongoing_vfolder_fails",
            "purge_delete_error_vfolder_fails",
        ],
    )
    async def test_purge_vfolder_invalid_status(
        self,
        test_case: dict[str, Any],
        etcd_fixture: None,
        mock_etcd_ctx: Any,
        mock_config_provider_ctx: Any,
        database_fixture: None,
        create_app_and_client: Any,
        get_headers: Any,
    ) -> None:
        """Test purge fails for non-PURGABLE vfolders."""
        app, client = await create_app_and_client(
            [
                mock_etcd_ctx,
                mock_config_provider_ctx,
                redis_ctx,
                database_ctx,
                storage_manager_ctx,
                repositories_ctx,
                monitoring_ctx,
                hook_plugin_ctx,
                mock_processors_ctx,
            ],
            [".vfolder", ".auth"],
        )

        url = "/folders/purge"
        params = {"vfolder_id": test_case["vfolder_id"]}
        req_bytes = json.dumps(params).encode()
        headers = get_headers("POST", url, req_bytes)

        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == HTTPStatus.BAD_REQUEST

        # Verify vfolder still exists in database
        await self._verify_vfolder_exists(app, test_case["vfolder_id"])

    # @pytest.mark.asyncio
    @pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_PURGE_VFOLDER_TEST, indirect=True)
    async def test_purge_vfolder_not_found(
        self,
        etcd_fixture: None,
        mock_etcd_ctx: Any,
        mock_config_provider_ctx: Any,
        database_fixture: None,
        create_app_and_client: Any,
        get_headers: Any,
    ) -> None:
        """Test purge fails for non-existent vfolder."""
        app, client = await create_app_and_client(
            [
                mock_etcd_ctx,
                mock_config_provider_ctx,
                redis_ctx,
                database_ctx,
                storage_manager_ctx,
                repositories_ctx,
                monitoring_ctx,
                hook_plugin_ctx,
                mock_processors_ctx,
            ],
            [".vfolder", ".auth"],
        )

        url = "/folders/purge"
        non_existent_id = "99999999-9999-9999-9999-999999999999"
        params = {"vfolder_id": non_existent_id}
        req_bytes = json.dumps(params).encode()
        headers = get_headers("POST", url, req_bytes)

        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == HTTPStatus.NOT_FOUND

    # @pytest.mark.asyncio
    @pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_PURGE_VFOLDER_TEST, indirect=True)
    async def test_purge_vfolder_insufficient_privilege(
        self,
        etcd_fixture: None,
        mock_etcd_ctx: Any,
        mock_config_provider_ctx: Any,
        database_fixture: None,
        create_app_and_client: Any,
        get_headers: Any,
        user_keypair: tuple[str, str],
    ) -> None:
        """Test purge fails for non-admin users."""
        app, client = await create_app_and_client(
            [
                mock_etcd_ctx,
                mock_config_provider_ctx,
                redis_ctx,
                database_ctx,
                storage_manager_ctx,
                repositories_ctx,
                monitoring_ctx,
                hook_plugin_ctx,
                mock_processors_ctx,
            ],
            [".vfolder", ".auth"],
        )

        url = "/folders/purge"
        params = {"vfolder_id": VFOLDER_DELETE_PENDING_ID}
        req_bytes = json.dumps(params).encode()
        # Use user_keypair instead of default admin keypair
        headers = get_headers("POST", url, req_bytes, keypair=user_keypair)

        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == HTTPStatus.FORBIDDEN

        # Verify vfolder still exists in database
        await self._verify_vfolder_exists(app, VFOLDER_DELETE_PENDING_ID)
