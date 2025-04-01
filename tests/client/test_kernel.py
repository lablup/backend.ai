import secrets
import uuid
from http import HTTPStatus
from unittest import mock

import pytest

from ai.backend.client.config import APIConfig
from ai.backend.client.session import Session, api_session
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


def test_create_with_config(mocker, api_version):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=HTTPStatus.CREATED,
        json=AsyncMock(
            return_value={
                "sessionId": str(uuid.uuid4()),
                "created": True,
            },
        ),
    )
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    myconfig = APIConfig(
        endpoint="https://localhost:9999",
        access_key="1234",
        secret_key="asdf",
        user_agent="BAIClientTest",
        version=f"v{api_version[0]}.{api_version[1]}",
    )
    with Session(config=myconfig) as session:
        prefix = get_naming(session.api_version, "path")
        if api_version[0] == 4:
            assert prefix == "kernel"
        else:
            assert prefix == "session"
        assert session.config is myconfig
        session.ComputeSession.get_or_create("python")
        mock_req.assert_called_once_with("POST", f"/{prefix}")
        current_api_session = api_session.get()
        assert str(current_api_session.config.endpoint) == "https://localhost:9999"
        assert current_api_session.config.user_agent == "BAIClientTest"
        assert current_api_session.config.access_key == "1234"
        assert current_api_session.config.secret_key == "asdf"


def test_create_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(
        status=HTTPStatus.CREATED,
        json=AsyncMock(
            return_value={
                "sessionId": str(uuid.uuid4()),
                "created": True,
            },
        ),
    )
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    with Session() as session:
        prefix = get_naming(session.api_version, "path")
        session.ComputeSession.get_or_create("python:3.6-ubuntu18.04")
        mock_req.assert_called_once_with("POST", f"/{prefix}")
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_destroy_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    with Session() as session:
        prefix = get_naming(session.api_version, "path")
        session_name = secrets.token_hex(12)
        cs = session.ComputeSession(session_name)
        cs.destroy()
        mock_req.assert_called_once_with("DELETE", f"/{prefix}/{session_name}", params={})
        mock_req_obj.fetch.assert_called_once_with()


def test_restart_kernel_url(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    with Session() as session:
        prefix = get_naming(session.api_version, "path")
        session_name = secrets.token_hex(12)
        cs = session.ComputeSession(session_name)
        cs.restart()
        mock_req.assert_called_once_with("PATCH", f"/{prefix}/{session_name}", params={})
        mock_req_obj.fetch.assert_called_once_with()


def test_get_kernel_info_url(mocker):
    return_value = {}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.OK, json=mock_json_coro)
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    with Session() as session:
        prefix = get_naming(session.api_version, "path")
        session_name = secrets.token_hex(12)
        cs = session.ComputeSession(session_name)
        cs.get_info()
        mock_req.assert_called_once_with("GET", f"/{prefix}/{session_name}", params={})
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()


def test_execute_code_url(mocker):
    return_value = {"result": "hi"}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.OK, json=mock_json_coro)
    mock_req = mocker.patch("ai.backend.client.func.session.Request", return_value=mock_req_obj)
    with Session() as session:
        prefix = get_naming(session.api_version, "path")
        session_name = secrets.token_hex(12)
        cs = session.ComputeSession(session_name)
        run_id = secrets.token_hex(8)
        cs.execute(run_id, "hello")
        mock_req.assert_called_once_with(
            "POST",
            f"/{prefix}/{session_name}",
            params={},
        )
        mock_req_obj.fetch.assert_called_once_with()
        mock_req_obj.fetch.return_value.json.assert_called_once_with()
