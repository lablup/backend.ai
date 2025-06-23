from http import HTTPStatus

import aiohttp
import pytest
from aiohttp import web

from ai.backend.client import config
from ai.backend.client.cli.proxy import create_proxy_app


@pytest.fixture
async def api_app_fixture(unused_tcp_port_factory):
    api_port = unused_tcp_port_factory()
    app = web.Application()
    recv_queue = []

    async def echo_ws(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                recv_queue.append(msg)
                await ws.send_str(msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                recv_queue.append(msg)
                await ws.send_bytes(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                recv_queue.append(msg)
        return ws

    async def echo_web(request):
        body = await request.read()
        resp = web.Response(status=HTTPStatus.OK, reason="Good", body=body)
        resp.headers["Content-Type"] = request.content_type
        return resp

    app.router.add_route("GET", r"/stream/echo", echo_ws)
    app.router.add_route("POST", r"/echo", echo_web)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", api_port)
    await site.start()
    try:
        yield app, recv_queue, api_port
    finally:
        await runner.cleanup()


@pytest.fixture
async def proxy_app_fixture(unused_tcp_port_factory):
    app = create_proxy_app()
    runner = web.AppRunner(app)
    proxy_port = unused_tcp_port_factory()
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", proxy_port)
    await site.start()
    try:
        yield app, proxy_port
    finally:
        await runner.cleanup()


@pytest.mark.xfail(
    reason="pytest-dev/pytest-asyncio#153 should be resolved to make this test working",
)
@pytest.mark.asyncio
async def test_proxy_web(
    monkeypatch,
    example_keypair,
    api_app_fixture,
    proxy_app_fixture,
):
    api_app, recv_queue, api_port = api_app_fixture
    api_url = "http://127.0.0.1:{}".format(api_port)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    monkeypatch.setattr(config, "_config", config.APIConfig())
    proxy_app, proxy_port = proxy_app_fixture
    proxy_timeout = aiohttp.ClientTimeout(connect=1.0)
    async with aiohttp.ClientSession(timeout=proxy_timeout) as proxy_client:
        proxy_url = "http://127.0.0.1:{}".format(proxy_port)
        data = {"test": 1234}
        async with proxy_client.request("POST", proxy_url + "/echo", json=data) as resp:
            assert resp.status == HTTPStatus.OK
            assert resp.reason == "Good"
            ret = await resp.json()
            assert ret["test"] == 1234


@pytest.mark.xfail(
    reason="pytest-dev/pytest-asyncio#153 should be resolved to make this test working",
)
@pytest.mark.asyncio
async def test_proxy_web_502(
    monkeypatch,
    example_keypair,
    proxy_app_fixture,
    unused_tcp_port_factory,
):
    api_port = unused_tcp_port_factory()
    api_url = "http://127.0.0.1:{}".format(api_port)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    monkeypatch.setattr(config, "_config", config.APIConfig())
    # Skip creation of api_app; let the proxy use a non-existent server.
    proxy_timeout = aiohttp.ClientTimeout(connect=1.0)
    async with aiohttp.ClientSession(timeout=proxy_timeout) as proxy_client:
        proxy_app, proxy_port = proxy_app_fixture
        proxy_url = "http://127.0.0.1:{}".format(proxy_port)
        data = {"test": 1234}
        async with proxy_client.request("POST", proxy_url + "/echo", json=data) as resp:
            assert resp.status == HTTPStatus.BAD_GATEWAY
            assert resp.reason == "Bad Gateway"


@pytest.mark.xfail(
    reason="pytest-dev/pytest-asyncio#153 should be resolved to make this test working",
)
@pytest.mark.asyncio
async def test_proxy_websocket(
    monkeypatch,
    example_keypair,
    api_app_fixture,
    proxy_app_fixture,
):
    api_app, recv_queue, api_port = api_app_fixture
    api_url = "http://127.0.0.1:{}".format(api_port)
    monkeypatch.setenv("BACKEND_ACCESS_KEY", example_keypair[0])
    monkeypatch.setenv("BACKEND_SECRET_KEY", example_keypair[1])
    monkeypatch.setenv("BACKEND_ENDPOINT", api_url)
    monkeypatch.setattr(config, "_config", config.APIConfig())
    proxy_timeout = aiohttp.ClientTimeout(connect=1.0)
    async with aiohttp.ClientSession(timeout=proxy_timeout) as proxy_client:
        proxy_app, proxy_port = proxy_app_fixture
        proxy_url = "http://127.0.0.1:{}".format(proxy_port)
        ws = await proxy_client.ws_connect(proxy_url + "/stream/echo")
        await ws.send_str("test")
        assert await ws.receive_str() == "test"
        await ws.send_bytes(b"\x00\x00")
        assert await ws.receive_bytes() == b"\x00\x00"
        assert recv_queue[0].type == aiohttp.WSMsgType.TEXT
        assert recv_queue[0].data == "test"
        assert recv_queue[1].type == aiohttp.WSMsgType.BINARY
        assert recv_queue[1].data == b"\x00\x00"
        await ws.close()
