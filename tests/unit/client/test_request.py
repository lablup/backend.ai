from __future__ import annotations

import io
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any
from unittest import mock
from unittest.mock import AsyncMock

import aiohttp
import pytest

from ai.backend.client.config import API_VERSION, get_config
from ai.backend.client.request import AttachedFile, Request
from ai.backend.client.session import AsyncSession, Session

if TYPE_CHECKING:
    from ai.backend.client.config import APIConfig


@pytest.fixture(scope="module", autouse=True)
def api_version() -> Iterator[None]:
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield


@pytest.fixture
def session(defconfig: APIConfig) -> Iterator[Session]:
    with Session(config=defconfig) as session:
        yield session


@pytest.fixture
def mock_request_params(session: Session) -> dict[str, Any]:
    return {
        "method": "GET",
        "path": "/function/item/",
        "params": {"app": "999"},
        "content": b'{"test1": 1}',
        "content_type": "application/json",
    }


def test_request_initialization(mock_request_params: dict[str, Any]) -> None:
    rqst = Request(**mock_request_params)

    assert rqst.method == mock_request_params["method"]
    assert rqst.params == mock_request_params["params"]
    assert rqst.path == mock_request_params["path"].lstrip("/")
    assert rqst.content == mock_request_params["content"]
    assert "X-BackendAI-Version" in rqst.headers


def test_request_set_content_none(mock_request_params: dict[str, Any]) -> None:
    mock_request_params = mock_request_params.copy()
    mock_request_params["content"] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b""
    assert rqst._pack_content() is rqst.content


def test_request_set_content(mock_request_params: dict[str, Any]) -> None:
    rqst = Request(**mock_request_params)
    assert rqst.content == mock_request_params["content"]
    assert rqst.content_type == "application/json"
    assert rqst._pack_content() is rqst.content

    mock_request_params["content"] = "hello"
    mock_request_params["content_type"] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b"hello"
    assert rqst.content_type == "text/plain"
    assert rqst._pack_content() is rqst.content

    mock_request_params["content"] = b"\x00\x01\xfe\xff"
    mock_request_params["content_type"] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b"\x00\x01\xfe\xff"
    assert rqst.content_type == "application/octet-stream"
    assert rqst._pack_content() is rqst.content


def test_request_attach_files(mock_request_params: dict[str, Any]) -> None:
    files = [
        AttachedFile("test1.txt", io.BytesIO(), "application/octet-stream"),
        AttachedFile("test2.txt", io.BytesIO(), "application/octet-stream"),
    ]

    mock_request_params["content"] = b"something"
    rqst = Request(**mock_request_params)
    with pytest.raises(ValueError):
        rqst.attach_files(files)

    mock_request_params["content"] = b""
    rqst = Request(**mock_request_params)
    rqst.attach_files(files)

    assert rqst.content_type == "multipart/form-data"
    assert rqst.content == b""
    packed_content = rqst._pack_content()
    assert isinstance(packed_content, aiohttp.FormData)
    assert packed_content.is_multipart


def test_build_correct_url(mock_request_params: dict[str, Any]) -> None:
    config = get_config()
    canonical_url = str(config.endpoint).rstrip("/") + "/function?app=999"

    mock_request_params["path"] = "/function"
    rqst = Request(**mock_request_params)
    assert str(rqst._build_url()) == canonical_url

    mock_request_params["path"] = "function"
    rqst = Request(**mock_request_params)
    assert str(rqst._build_url()) == canonical_url


async def test_fetch_invalid_method(mock_request_params: dict[str, Any]) -> None:
    mock_request_params["method"] = "STRANGE"
    rqst = Request(**mock_request_params)

    with pytest.raises(ValueError):
        async with rqst.fetch():
            pass


async def test_fetch_invalid_method_async() -> None:
    async with AsyncSession():
        rqst = Request("STRANGE", "/")
        with pytest.raises(ValueError):
            async with rqst.fetch():
                pass
