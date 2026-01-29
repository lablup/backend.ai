"""
Tests for groupconfig.py API handlers.

These tests verify the handler layer that uses Repository and Processor patterns.
"""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.storage import (
    DotfileAlreadyExists,
    DotfileCreationFailed,
    DotfileNotFound,
)
from ai.backend.manager.models.group import GroupDotfile
from ai.backend.manager.services.group_config.actions.create_dotfile import (
    CreateDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.delete_dotfile import (
    DeleteDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.get_dotfile import (
    GetDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.list_dotfiles import (
    ListDotfilesActionResult,
)
from ai.backend.manager.services.group_config.actions.update_dotfile import (
    UpdateDotfileActionResult,
)

if TYPE_CHECKING:
    from aiohttp.test_utils import TestClient


from ai.backend.manager.api import groupconfig

# Get handler functions
create_handler = groupconfig.create
list_or_get_handler = groupconfig.list_or_get
update_handler = groupconfig.update
delete_handler = groupconfig.delete


@pytest.fixture
def group_id() -> uuid.UUID:
    """Create test group UUID."""
    return uuid.uuid4()


@pytest.fixture
def domain_name() -> str:
    """Create test domain name."""
    return "test-domain"


@pytest.fixture
def sample_dotfiles() -> list[GroupDotfile]:
    """Create sample dotfiles data."""
    return [
        {"path": ".bashrc", "perm": "644", "data": "# bashrc content"},
        {"path": ".vimrc", "perm": "644", "data": '" vimrc content'},
    ]


@pytest.fixture
def mock_root_ctx() -> MagicMock:
    """Create RootContext mock with processors."""
    from ai.backend.manager.api import ManagerStatus

    ctx = MagicMock()

    # Mock config_provider for @server_status_required decorator
    ctx.config_provider.legacy_etcd_config_loader.get_manager_status = AsyncMock(
        return_value=ManagerStatus.RUNNING
    )

    # Mock processors only - handler no longer references repositories directly
    ctx.processors.group_config.create_dotfile.wait_for_complete = AsyncMock()
    ctx.processors.group_config.list_dotfiles.wait_for_complete = AsyncMock()
    ctx.processors.group_config.get_dotfile.wait_for_complete = AsyncMock()
    ctx.processors.group_config.update_dotfile.wait_for_complete = AsyncMock()
    ctx.processors.group_config.delete_dotfile.wait_for_complete = AsyncMock()

    return ctx


@pytest.fixture
def admin_middleware(
    mock_root_ctx: MagicMock,
    domain_name: str,
) -> Middleware:
    """Create middleware that sets admin authentication context."""

    @web.middleware
    async def middleware(request: web.Request, handler: Any) -> web.StreamResponse:
        request.app["_root.context"] = mock_root_ctx
        request["user"] = {
            "uuid": uuid.uuid4(),
            "email": "admin@example.com",
            "domain_name": domain_name,
        }
        request["keypair"] = {"access_key": "TESTKEY"}
        request["is_authorized"] = True
        request["is_admin"] = True
        request["is_superadmin"] = False
        return await handler(request)

    return middleware


@pytest.fixture
def app_with_admin(admin_middleware: Middleware) -> web.Application:
    """Create aiohttp app with admin routes."""
    app = web.Application(middlewares=[admin_middleware])
    app.router.add_post("/group-config/dotfiles", create_handler)
    app.router.add_get("/group-config/dotfiles", list_or_get_handler)
    app.router.add_patch("/group-config/dotfiles", update_handler)
    app.router.add_delete("/group-config/dotfiles", delete_handler)
    return app


class TestCreateDotfile:
    """Tests for create dotfile endpoint."""

    @pytest.mark.asyncio
    async def test_create_dotfile_success(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test successful dotfile creation."""
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.return_value = (
            CreateDotfileActionResult(group_id=group_id)
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.post(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".bashrc",
                "data": "# new bashrc",
                "permission": "644",
            },
        )

        assert resp.status == HTTPStatus.OK
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dotfile_duplicate_path(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test dotfile creation fails when path already exists."""
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.side_effect = (
            DotfileAlreadyExists
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.post(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".bashrc",
                "data": "# duplicate",
                "permission": "644",
            },
        )

        # DotfileAlreadyExists inherits from HTTPBadRequest
        assert resp.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_dotfile_limit_reached(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test dotfile creation fails when limit (100) is reached."""
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.side_effect = (
            DotfileCreationFailed("Dotfile creation limit reached")
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.post(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".newfile",
                "data": "# content",
                "permission": "644",
            },
        )

        assert resp.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_dotfile_no_leftover_space(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test dotfile creation fails when no leftover space."""
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.side_effect = (
            DotfileCreationFailed("No leftover space for dotfile storage")
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.post(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".bashrc",
                "data": "# content",
                "permission": "644",
            },
        )

        assert resp.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_dotfile_group_not_found(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test dotfile creation fails when group not found."""
        mock_root_ctx.processors.group_config.create_dotfile.wait_for_complete.side_effect = (
            ProjectNotFound
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.post(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".bashrc",
                "data": "# content",
                "permission": "644",
            },
        )

        assert resp.status == HTTPStatus.NOT_FOUND


class TestListOrGetDotfile:
    """Tests for list/get dotfile endpoint."""

    @pytest.mark.asyncio
    async def test_list_dotfiles_success(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
        sample_dotfiles: list[GroupDotfile],
    ) -> None:
        """Test listing all dotfiles for a group."""
        mock_root_ctx.processors.group_config.list_dotfiles.wait_for_complete.return_value = (
            ListDotfilesActionResult(dotfiles=sample_dotfiles)
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.get(
            "/group-config/dotfiles",
            params={"group": str(group_id)},
        )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert len(data) == 2
        assert data[0]["path"] == ".bashrc"
        # Verify response format transformation (perm -> permission)
        assert "permission" in data[0]
        assert data[0]["permission"] == "644"

    @pytest.mark.asyncio
    async def test_get_single_dotfile_success(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test getting a single dotfile by path."""
        dotfile: GroupDotfile = {"path": ".bashrc", "perm": "644", "data": "# bashrc content"}
        mock_root_ctx.processors.group_config.get_dotfile.wait_for_complete.return_value = (
            GetDotfileActionResult(dotfile=dotfile)
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.get(
            "/group-config/dotfiles",
            params={"group": str(group_id), "path": ".bashrc"},
        )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["path"] == ".bashrc"

    @pytest.mark.asyncio
    async def test_get_dotfile_not_found(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test getting non-existent dotfile returns 404."""
        mock_root_ctx.processors.group_config.get_dotfile.wait_for_complete.side_effect = (
            DotfileNotFound
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.get(
            "/group-config/dotfiles",
            params={"group": str(group_id), "path": ".nonexistent"},
        )

        assert resp.status == HTTPStatus.NOT_FOUND


class TestUpdateDotfile:
    """Tests for update dotfile endpoint."""

    @pytest.mark.asyncio
    async def test_update_dotfile_success(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test successful dotfile update."""
        mock_root_ctx.processors.group_config.update_dotfile.wait_for_complete.return_value = (
            UpdateDotfileActionResult(group_id=group_id)
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.patch(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".bashrc",
                "data": "# updated content",
                "permission": "755",
            },
        )

        assert resp.status == HTTPStatus.OK
        mock_root_ctx.processors.group_config.update_dotfile.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dotfile_not_found(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test updating non-existent dotfile returns 404."""
        mock_root_ctx.processors.group_config.update_dotfile.wait_for_complete.side_effect = (
            DotfileNotFound
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.patch(
            "/group-config/dotfiles",
            json={
                "group": str(group_id),
                "path": ".nonexistent",
                "data": "# content",
                "permission": "644",
            },
        )

        assert resp.status == HTTPStatus.NOT_FOUND


class TestDeleteDotfile:
    """Tests for delete dotfile endpoint."""

    @pytest.mark.asyncio
    async def test_delete_dotfile_success(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test successful dotfile deletion."""
        mock_root_ctx.processors.group_config.delete_dotfile.wait_for_complete.return_value = (
            DeleteDotfileActionResult(success=True)
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.delete(
            "/group-config/dotfiles",
            params={
                "group": str(group_id),
                "path": ".bashrc",
            },
        )

        assert resp.status == HTTPStatus.OK
        data = await resp.json()
        assert data["success"] is True
        mock_root_ctx.processors.group_config.delete_dotfile.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dotfile_not_found(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test deleting non-existent dotfile returns 404."""
        mock_root_ctx.processors.group_config.delete_dotfile.wait_for_complete.side_effect = (
            DotfileNotFound
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.delete(
            "/group-config/dotfiles",
            params={
                "group": str(group_id),
                "path": ".nonexistent",
            },
        )

        assert resp.status == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_dotfile_group_not_found(
        self,
        aiohttp_client: Any,
        app_with_admin: web.Application,
        mock_root_ctx: MagicMock,
        group_id: uuid.UUID,
    ) -> None:
        """Test deleting dotfile from non-existent group returns 404."""
        mock_root_ctx.processors.group_config.delete_dotfile.wait_for_complete.side_effect = (
            ProjectNotFound
        )

        client: TestClient = await aiohttp_client(app_with_admin)
        resp = await client.delete(
            "/group-config/dotfiles",
            params={
                "group": str(group_id),
                "path": ".bashrc",
            },
        )

        assert resp.status == HTTPStatus.NOT_FOUND
