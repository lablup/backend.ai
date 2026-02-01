from __future__ import annotations

from collections.abc import Iterator
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session
from ai.backend.testutils.mock import AsyncContextMock

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(scope="module", autouse=True)
def api_version() -> Iterator[tuple[int, str]]:
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield API_VERSION


def test_status(mocker: MockerFixture) -> None:
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


def test_freeze(mocker: MockerFixture) -> None:
    mock_req_obj = mocker.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze()  # type: ignore[unused-coroutine]
        mock_req_obj.fetch.assert_called_once_with()


def test_freeze_opt_force_kill(mocker: MockerFixture) -> None:
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.freeze(force_kill=True)  # type: ignore[unused-coroutine]
        mock_req_obj.fetch.assert_called_once_with()


def test_unfreeze(mocker: MockerFixture) -> None:
    mock_req_obj = mock.Mock()
    mock_req_obj.fetch.return_value = AsyncContextMock(status=HTTPStatus.NO_CONTENT)
    mocker.patch("ai.backend.client.func.manager.Request", return_value=mock_req_obj)

    with Session() as session:
        session.Manager.unfreeze()  # type: ignore[unused-coroutine]
        mock_req_obj.fetch.assert_called_once_with()
