import logging
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER, request_id_middleware
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.api.manager import get_quota_scope, get_vfolder_usage

VOLUME_NAME = "local"
REQUEST_ID = "req-from-manager"
QUOTA_SCOPE_ID = QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=uuid.uuid4())
FOLDER_ID = uuid.uuid4()
BACKEND_LOGGER = "tests.storage_proxy.backend"

backend_log = StructuredLogger(logging.getLogger(BACKEND_LOGGER))


def _backend_call(result: Any) -> AsyncMock:
    async def _call(*args: Any, **kwargs: Any) -> Any:
        backend_log.warning("negative quota usage reported")
        return result

    return AsyncMock(side_effect=_call)


@pytest.fixture
def volume() -> MagicMock:
    volume = MagicMock()
    volume.quota_model.describe_quota_scope = _backend_call(MagicMock(used_bytes=1, limit_bytes=2))
    volume.get_usage = _backend_call(MagicMock(file_count=1, used_bytes=1))
    return volume


@pytest.fixture
async def client(aiohttp_client: Any, volume: MagicMock) -> Any:
    app = web.Application(middlewares=[request_id_middleware])
    root_ctx = MagicMock()
    root_ctx.volume_pool.get_volume_by_name.return_value = volume
    app["ctx"] = root_ctx
    app.router.add_post("/quota-scope", get_quota_scope)
    app.router.add_post("/folder/usage", get_vfolder_usage)
    return await aiohttp_client(app)


class TestManagerAPILogScope:
    async def test_quota_scope_handler_scopes_backend_logs(
        self, client: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger=BACKEND_LOGGER):
            resp = await client.post(
                "/quota-scope",
                json={"volume": VOLUME_NAME, "qsid": str(QUOTA_SCOPE_ID)},
                headers={REQUEST_ID_HEADER: REQUEST_ID},
            )

        assert resp.status == 200
        [record] = [r for r in caplog.records if r.name == BACKEND_LOGGER]
        assert record.__dict__["log_tag_request_id"] == REQUEST_ID
        assert "log_tag_volume_id" not in record.__dict__
        assert record.__dict__["log_tag_volume_name"] == VOLUME_NAME
        assert record.__dict__["log_tag_quota_scope_id"] == str(QUOTA_SCOPE_ID)

    async def test_vfolder_handler_scopes_backend_logs(
        self, client: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        vfolder_id = VFolderID(quota_scope_id=QUOTA_SCOPE_ID, folder_id=FOLDER_ID)
        with caplog.at_level(logging.WARNING, logger=BACKEND_LOGGER):
            resp = await client.post(
                "/folder/usage",
                json={"volume": VOLUME_NAME, "vfid": str(vfolder_id)},
                headers={REQUEST_ID_HEADER: REQUEST_ID},
            )

        assert resp.status == 200
        [record] = [r for r in caplog.records if r.name == BACKEND_LOGGER]
        assert record.__dict__["log_tag_request_id"] == REQUEST_ID
        assert "log_tag_volume_id" not in record.__dict__
        assert record.__dict__["log_tag_volume_name"] == VOLUME_NAME
        assert record.__dict__["log_tag_vfolder_id"] == str(FOLDER_ID)
