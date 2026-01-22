"""
Tests for group API handlers (project registry quota).

Tests trafaret-based validation via HTTP requests using aiohttp_client.
When migrating to pydantic with @api_handler decorator:
- Keep the same test structure
- Add ProcessorsCtx/RequestCtx middleware param patches
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from aiohttp.typedefs import Middleware

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.group import (
    create_project_registry_quota,
    delete_project_registry_quota,
    read_project_registry_quota,
    update_project_registry_quota,
)
from ai.backend.manager.services.project_registry_quota.actions.create_project_registry_quota import (
    CreateProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.delete_project_registry_quota import (
    DeleteProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.read_project_registry_quota import (
    ReadProjectRegistryQuotaActionResult,
)
from ai.backend.manager.services.project_registry_quota.actions.update_project_registry_quota import (
    UpdateProjectRegistryQuotaActionResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_processors() -> MagicMock:
    """Create mock processors with project_registry_quota action processors."""
    processors = MagicMock()
    processors.project_registry_quota = MagicMock()
    processors.project_registry_quota.create_project_registry_quota = MagicMock()
    processors.project_registry_quota.read_project_registry_quota = MagicMock()
    processors.project_registry_quota.update_project_registry_quota = MagicMock()
    processors.project_registry_quota.delete_project_registry_quota = MagicMock()
    return processors


@pytest.fixture
def mock_root_ctx(mock_processors: MagicMock) -> MagicMock:
    """RootContext mock with processors and config_provider."""

    root_ctx = MagicMock()
    root_ctx.processors = mock_processors
    # Mock for server_status_required decorator
    root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status = AsyncMock(
        return_value=ManagerStatus.RUNNING
    )
    return root_ctx


@pytest.fixture
def superadmin_middleware() -> Middleware:
    """Create middleware that sets superadmin authentication context."""

    @web.middleware
    async def middleware(request: web.Request, handler: Any) -> web.StreamResponse:
        request["is_authorized"] = True
        request["is_admin"] = True
        request["is_superadmin"] = True
        request["user"] = {
            "uuid": uuid4(),
            "email": "superadmin@example.com",
            "domain_name": "default",
        }
        request["keypair"] = {"access_key": "SUPERADMINKEY"}
        return await handler(request)

    return middleware


@pytest.fixture
def app(
    mock_root_ctx: MagicMock,
    superadmin_middleware: Middleware,
) -> web.Application:
    """Create aiohttp app with group handler routes."""
    app = web.Application(middlewares=[superadmin_middleware])
    app["_root.context"] = mock_root_ctx

    app.router.add_post("/group/registry-quota", create_project_registry_quota)
    app.router.add_get("/group/registry-quota", read_project_registry_quota)
    app.router.add_patch("/group/registry-quota", update_project_registry_quota)
    app.router.add_delete("/group/registry-quota", delete_project_registry_quota)

    return app


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestCreateProjectRegistryQuota:
    """Tests for create_project_registry_quota handler."""

    @pytest.fixture
    def group_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def create_result(self, group_id: UUID) -> CreateProjectRegistryQuotaActionResult:
        return CreateProjectRegistryQuotaActionResult(project_id=group_id)

    @pytest.mark.asyncio
    async def test_create_project_registry_quota_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        group_id: UUID,
        create_result: CreateProjectRegistryQuotaActionResult,
    ) -> None:
        """Verify processor is called with correct params and returns HTTP 204."""
        quota = 1024 * 1024 * 1024  # 1GB
        mock_processors.project_registry_quota.create_project_registry_quota.wait_for_complete = (
            AsyncMock(return_value=create_result)
        )

        client: TestClient = await aiohttp_client(app)
        resp = await client.post(
            "/group/registry-quota",
            json={"group_id": str(group_id), "quota": quota},
        )

        assert resp.status == HTTPStatus.NO_CONTENT
        mock_processors.project_registry_quota.create_project_registry_quota.wait_for_complete.assert_called_once()
        action = mock_processors.project_registry_quota.create_project_registry_quota.wait_for_complete.call_args[
            0
        ][0]
        assert action.project_id == group_id
        assert action.quota == quota

    @pytest.mark.asyncio
    async def test_create_project_registry_quota_accepts_group_alias(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        group_id: UUID,
        create_result: CreateProjectRegistryQuotaActionResult,
    ) -> None:
        """Verify 'group' alias for 'group_id' is accepted."""
        quota = 1024
        mock_processors.project_registry_quota.create_project_registry_quota.wait_for_complete = (
            AsyncMock(return_value=create_result)
        )

        client: TestClient = await aiohttp_client(app)
        resp = await client.post(
            "/group/registry-quota",
            json={"group": str(group_id), "quota": quota},  # alias
        )

        assert resp.status == HTTPStatus.NO_CONTENT
        action = mock_processors.project_registry_quota.create_project_registry_quota.wait_for_complete.call_args[
            0
        ][0]
        assert action.project_id == group_id


class TestReadProjectRegistryQuota:
    """Tests for read_project_registry_quota handler."""

    @pytest.fixture
    def group_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def read_result(self, group_id: UUID) -> ReadProjectRegistryQuotaActionResult:
        return ReadProjectRegistryQuotaActionResult(
            project_id=group_id, quota=5 * 1024 * 1024 * 1024
        )

    @pytest.mark.asyncio
    async def test_read_project_registry_quota_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        group_id: UUID,
        read_result: ReadProjectRegistryQuotaActionResult,
    ) -> None:
        """Verify processor is called and quota is returned."""
        mock_processors.project_registry_quota.read_project_registry_quota.wait_for_complete = (
            AsyncMock(return_value=read_result)
        )

        client: TestClient = await aiohttp_client(app)
        resp = await client.get(
            "/group/registry-quota",
            params={"group_id": str(group_id)},
        )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["result"] == read_result.quota
        mock_processors.project_registry_quota.read_project_registry_quota.wait_for_complete.assert_called_once()
        action = mock_processors.project_registry_quota.read_project_registry_quota.wait_for_complete.call_args[
            0
        ][0]
        assert action.project_id == group_id


class TestUpdateProjectRegistryQuota:
    """Tests for update_project_registry_quota handler."""

    @pytest.fixture
    def group_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def update_result(self, group_id: UUID) -> UpdateProjectRegistryQuotaActionResult:
        return UpdateProjectRegistryQuotaActionResult(project_id=group_id)

    @pytest.mark.asyncio
    async def test_update_project_registry_quota_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        group_id: UUID,
        update_result: UpdateProjectRegistryQuotaActionResult,
    ) -> None:
        """Verify processor is called with correct params and returns HTTP 204."""
        new_quota = 10 * 1024 * 1024 * 1024  # 10GB
        mock_processors.project_registry_quota.update_project_registry_quota.wait_for_complete = (
            AsyncMock(return_value=update_result)
        )

        client: TestClient = await aiohttp_client(app)
        resp = await client.patch(
            "/group/registry-quota",
            json={"group_id": str(group_id), "quota": new_quota},
        )

        assert resp.status == HTTPStatus.NO_CONTENT
        mock_processors.project_registry_quota.update_project_registry_quota.wait_for_complete.assert_called_once()
        action = mock_processors.project_registry_quota.update_project_registry_quota.wait_for_complete.call_args[
            0
        ][0]
        assert action.project_id == group_id
        assert action.quota == new_quota


class TestDeleteProjectRegistryQuota:
    """Tests for delete_project_registry_quota handler."""

    @pytest.fixture
    def group_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def delete_result(self, group_id: UUID) -> DeleteProjectRegistryQuotaActionResult:
        return DeleteProjectRegistryQuotaActionResult(project_id=group_id)

    @pytest.mark.asyncio
    async def test_delete_project_registry_quota_success(
        self,
        aiohttp_client: Any,
        app: web.Application,
        mock_processors: MagicMock,
        group_id: UUID,
        delete_result: DeleteProjectRegistryQuotaActionResult,
    ) -> None:
        """Verify processor is called and returns HTTP 204."""
        mock_processors.project_registry_quota.delete_project_registry_quota.wait_for_complete = (
            AsyncMock(return_value=delete_result)
        )

        client: TestClient = await aiohttp_client(app)
        resp = await client.delete(
            "/group/registry-quota",
            json={"group_id": str(group_id)},
        )

        assert resp.status == HTTPStatus.NO_CONTENT
        mock_processors.project_registry_quota.delete_project_registry_quota.wait_for_complete.assert_called_once()
        action = mock_processors.project_registry_quota.delete_project_registry_quota.wait_for_complete.call_args[
            0
        ][0]
        assert action.project_id == group_id
