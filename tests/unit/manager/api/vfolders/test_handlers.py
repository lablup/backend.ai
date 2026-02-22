from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import vfolder as vfolder_module
from ai.backend.manager.api.vfolder import create_archive_download_session
from ai.backend.manager.models.vfolder import VFolderOperationStatus
from ai.backend.manager.services.vfolder.actions.file import (
    CreateArchiveDownloadSessionAction,
)

# --- Shared fixtures ---


@pytest.fixture
def mock_root_ctx() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status = AsyncMock(
        return_value=ManagerStatus.RUNNING,
    )
    return root_ctx


@pytest.fixture
def sample_vfolder_row() -> dict[str, Any]:
    return {
        "id": uuid.uuid4(),
        "host": "local:volume1",
        "status": VFolderOperationStatus.READY,
        "user": uuid.uuid4(),
        "user_email": "test@example.com",
        "group": None,
        "group_name": None,
    }


@pytest.fixture
async def client(
    aiohttp_client: Any,
    mock_root_ctx: MagicMock,
    sample_vfolder_row: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> Any:
    @web.middleware
    async def mock_auth_middleware(
        request: web.Request,
        handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
    ) -> web.StreamResponse:
        request["is_authorized"] = True
        request["user"] = {"uuid": uuid.uuid4(), "email": "test@example.com"}
        request["keypair"] = {
            "access_key": "TESTKEY",
            "resource_policy": {"allowed_vfolder_hosts": ["local"]},
        }
        return await handler(request)

    monkeypatch.setattr(
        vfolder_module,
        "resolve_vfolder_rows",
        AsyncMock(return_value=[sample_vfolder_row]),
    )

    app = web.Application(middlewares=[mock_auth_middleware])
    app["_root.context"] = mock_root_ctx
    app.router.add_post(
        "/folders/{name}/request-download-archive",
        create_archive_download_session,
    )
    return await aiohttp_client(app)


# --- Test classes (scenarios) ---


class TestCreateArchiveDownloadSession:
    """Tests for create_archive_download_session handler via aiohttp client."""

    EXPECTED_TOKEN = "test-token"
    EXPECTED_URL = "https://storage/download-archive"
    REQUEST_FILES = ["a.txt", "b/c.txt"]

    async def test_constructs_action_and_returns_token(
        self,
        client: Any,
        mock_root_ctx: MagicMock,
        sample_vfolder_row: dict[str, Any],
    ) -> None:
        """Test that handler returns token/url from processor result."""
        mock_processor = AsyncMock(
            return_value=MagicMock(token=self.EXPECTED_TOKEN, url=self.EXPECTED_URL),
        )
        mock_root_ctx.processors.vfolder_file.create_archive_download_session.wait_for_complete = (
            mock_processor
        )

        resp = await client.post(
            "/folders/test-vfolder/request-download-archive",
            json={"files": self.REQUEST_FILES},
        )

        assert resp.status == 200
        body = await resp.json()
        assert body == {"token": self.EXPECTED_TOKEN, "url": self.EXPECTED_URL}

        action = mock_processor.call_args.args[0]
        assert isinstance(action, CreateArchiveDownloadSessionAction)
        assert action.vfolder_uuid == sample_vfolder_row["id"]
        assert action.files == self.REQUEST_FILES
