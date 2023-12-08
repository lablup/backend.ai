import asyncio
import io
import json
from unittest import mock

import aiohttp
import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION, get_config
from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.request import AttachedFile, Request, Response
from ai.backend.client.session import AsyncSession, Session
from ai.backend.testutils.mock import AsyncMock


@pytest.fixture(scope="module", autouse=True)
def api_version():
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield


@pytest.fixture
def session(defconfig):
    with Session(config=defconfig) as session:
        yield session


@pytest.fixture
def mock_request_params(session):
    yield {
        "method": "GET",
        "path": "/function/item/",
        "params": {"app": "999"},
        "content": b'{"test1": 1}',
        "content_type": "application/json",
    }


def test_request_initialization(mock_request_params):
    rqst = Request(**mock_request_params)

    assert rqst.method == mock_request_params["method"]
    assert rqst.params == mock_request_params["params"]
    assert rqst.path == mock_request_params["path"].lstrip("/")
    assert rqst.content == mock_request_params["content"]
    assert "X-BackendAI-Version" in rqst.headers


def test_request_set_content_none(mock_request_params):
    mock_request_params = mock_request_params.copy()
    mock_request_params["content"] = None
    rqst = Request(**mock_request_params)
    assert rqst.content == b""
    assert rqst._pack_content() is rqst.content


def test_request_set_content(mock_request_params):
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


def test_request_attach_files(mock_request_params):
    files = [
        AttachedFile("test1.txt", io.BytesIO(), "application/octet-stream"),
        AttachedFile("test2.txt", io.BytesIO(), "application/octet-stream"),
    ]

    mock_request_params["content"] = b"something"
    rqst = Request(**mock_request_params)
    with pytest.raises(AssertionError):
        rqst.attach_files(files)

    mock_request_params["content"] = b""
    rqst = Request(**mock_request_params)
    rqst.attach_files(files)

    assert rqst.content_type == "multipart/form-data"
    assert rqst.content == b""
    packed_content = rqst._pack_content()
    assert packed_content.is_multipart


def test_build_correct_url(mock_request_params):
    config = get_config()
    canonical_url = str(config.endpoint).rstrip("/") + "/function?app=999"

    mock_request_params["path"] = "/function"
    rqst = Request(**mock_request_params)
    assert str(rqst._build_url()) == canonical_url

    mock_request_params["path"] = "function"
    rqst = Request(**mock_request_params)
    assert str(rqst._build_url()) == canonical_url


@pytest.mark.asyncio
async def test_fetch_invalid_method(mock_request_params):
    mock_request_params["method"] = "STRANGE"
    rqst = Request(**mock_request_params)

    with pytest.raises(AssertionError):
        async with rqst.fetch():
            pass


@pytest.mark.asyncio
async def test_fetch(dummy_endpoint):
    with aioresponses() as m, Session():
        body = b"hello world"
        m.post(
            dummy_endpoint + "function",
            status=200,
            body=body,
            headers={"Content-Type": "text/plain; charset=utf-8", "Content-Length": str(len(body))},
        )
        rqst = Request("POST", "function")
        async with rqst.fetch() as resp:
            assert isinstance(resp, Response)
            assert resp.status == 200
            assert resp.content_type == "text/plain"
            assert await resp.text() == body.decode()
            assert resp.content_length == len(body)

    with aioresponses() as m, Session():
        body = b'{"a": 1234, "b": null}'
        m.post(
            dummy_endpoint + "function",
            status=200,
            body=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(body)),
            },
        )
        rqst = Request("POST", "function")
        async with rqst.fetch() as resp:
            assert isinstance(resp, Response)
            assert resp.status == 200
            assert resp.content_type == "application/json"
            assert await resp.text() == body.decode()
            assert await resp.json() == {"a": 1234, "b": None}
            assert resp.content_length == len(body)


@pytest.mark.asyncio
async def test_streaming_fetch(dummy_endpoint):
    # Read content by chunks.
    with aioresponses() as m, Session():
        body = b"hello world"
        m.post(
            dummy_endpoint + "function",
            status=200,
            body=body,
            headers={"Content-Type": "text/plain; charset=utf-8", "Content-Length": str(len(body))},
        )
        rqst = Request("POST", "function")
        async with rqst.fetch() as resp:
            assert resp.status == 200
            assert resp.content_type == "text/plain"
            assert await resp.read(3) == b"hel"
            assert await resp.read(2) == b"lo"
            await resp.read()
            with pytest.raises(AssertionError):
                assert await resp.text()


@pytest.mark.asyncio
async def test_invalid_requests(dummy_endpoint):
    with aioresponses() as m, Session():
        body = json.dumps({
            "type": "https://api.backend.ai/probs/kernel-not-found",
            "title": "Kernel Not Found",
        }).encode("utf8")
        m.post(
            dummy_endpoint,
            status=404,
            body=body,
            headers={
                "Content-Type": "application/problem+json; charset=utf-8",
                "Content-Length": str(len(body)),
            },
        )
        rqst = Request("POST", "/")
        with pytest.raises(BackendAPIError) as e:
            async with rqst.fetch():
                pass
            assert e.status == 404
            assert e.data["type"] == "https://api.backend.ai/probs/kernel-not-found"
            assert e.data["title"] == "Kernel Not Found"


@pytest.mark.asyncio
async def test_fetch_invalid_method_async():
    async with AsyncSession():
        rqst = Request("STRANGE", "/")
        with pytest.raises(AssertionError):
            async with rqst.fetch():
                pass


@pytest.mark.asyncio
async def test_fetch_client_error_async(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession():
            m.post(dummy_endpoint, exception=aiohttp.ClientConnectionError())
            rqst = Request("POST", "/")
            with pytest.raises(BackendClientError):
                async with rqst.fetch():
                    pass


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_fetch_cancellation_async(dummy_endpoint):
    # It seems that aiohttp swallows asyncio.CancelledError
    with aioresponses() as m:
        async with AsyncSession():
            m.post(dummy_endpoint, exception=asyncio.CancelledError())
            rqst = Request("POST", "/")
            with pytest.raises(asyncio.CancelledError):
                async with rqst.fetch():
                    pass


@pytest.mark.asyncio
async def test_fetch_timeout_async(dummy_endpoint):
    with aioresponses() as m:
        async with AsyncSession():
            m.post(dummy_endpoint, exception=asyncio.TimeoutError())
            rqst = Request("POST", "/")
            with pytest.raises(asyncio.TimeoutError):
                async with rqst.fetch():
                    pass


@pytest.mark.asyncio
async def test_response_async(defconfig, dummy_endpoint):
    body = b'{"test": 5678}'
    with aioresponses() as m:
        m.post(
            dummy_endpoint + "function",
            status=200,
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        async with AsyncSession(config=defconfig):
            rqst = Request("POST", "/function")
            async with rqst.fetch() as resp:
                assert await resp.text() == '{"test": 5678}'
                assert await resp.json() == {"test": 5678}
