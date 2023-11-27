import secrets
import uuid
from unittest import mock

import pytest

from ai.backend.client.session import AsyncSession
from ai.backend.client.versioning import get_naming
from ai.backend.testutils.mock import AsyncContextMock, AsyncMock

simulated_api_versions = [
    (4, "20190615"),
    (5, "20191215"),
    (6, "20200815"),
]


@pytest.fixture(scope="module", autouse=True, params=simulated_api_versions)
def api_version(request):
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = request.param
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield request.param


@pytest.mark.asyncio
async def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=201,
        json=AsyncMock(
            return_value={
                "sessionId": str(uuid.uuid4()),
                "created": True,
            },
        ),
    )
    mock_req_cls = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    async with AsyncSession() as session:
        await session.ComputeSession.get_or_create("python:3.6-ubuntu18.04")
        prefix = get_naming(session.api_version, "path")
        mock_req_cls.assert_called_once_with("POST", f"/{prefix}")
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    session_name = secrets.token_hex(12)
    mock_req_cls = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    async with AsyncSession() as session:
        prefix = get_naming(session.api_version, "path")
        await session.ComputeSession(session_name).destroy()
        mock_req_cls.assert_called_once_with("DELETE", f"/{prefix}/{session_name}", params={})


@pytest.mark.asyncio
async def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=204)
    session_name = secrets.token_hex(12)
    mock_req_cls = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    async with AsyncSession() as session:
        prefix = get_naming(session.api_version, "path")
        await session.ComputeSession(session_name).restart()
        mock_req_cls.assert_called_once_with("PATCH", f"/{prefix}/{session_name}", params={})


@pytest.mark.asyncio
async def test_get_kernel_info_url(mocker):
    return_value = {}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=200, json=mock_json_coro)
    session_name = secrets.token_hex(12)
    mock_req_cls = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    async with AsyncSession() as session:
        prefix = get_naming(session.api_version, "path")
        await session.ComputeSession(session_name).get_info()
        mock_req_cls.assert_called_once_with("GET", f"/{prefix}/{session_name}", params={})


@pytest.mark.asyncio
async def test_execute_code_url(mocker):
    return_value = {"result": "hi"}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=200, json=mock_json_coro)
    session_name = secrets.token_hex(12)
    run_id = secrets.token_hex(8)
    mock_req_cls = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    async with AsyncSession() as session:
        prefix = get_naming(session.api_version, "path")
        await session.ComputeSession(session_name).execute(run_id, "hello")
        mock_req_cls.assert_called_once_with("POST", f"/{prefix}/{session_name}", params={})
