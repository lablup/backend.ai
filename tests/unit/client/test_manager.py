from http import HTTPStatus
from unittest import mock

import pytest

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session
from ai.backend.testutils.mock import AsyncContextMock, AsyncMock


@pytest.fixture(scope="module", autouse=True)
def api_version():
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield


def test_status(mocker):
    return_value = {"status": "running", "active_sessions": 3}
    mock_json_coro = AsyncMock(return_value=return_value)
    mock_req_obj = mocker.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.OK, json=mock_json_coro)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        resp = session.Manager.status()
        mock_req_obj.fetch.assert_called_once_with()
        assert resp["status"] == return_value["status"]
        assert resp["active_sessions"] == return_value["active_sessions"]


def test_freeze(mocker):
    mock_req_obj = mocker.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze()
        mock_req_obj.fetch.assert_called_once_with()


def test_freeze_opt_force_kill(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze(force_kill=True)
        mock_req_obj.fetch.assert_called_once_with()


def test_unfreeze(mocker):
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.unfreeze()
        mock_req_obj.fetch.assert_called_once_with()
