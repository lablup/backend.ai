import uuid

from aiohttp import web

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER, request_id_middleware


async def test_request_id_middleware_with_custom_request_id(aiohttp_client):
    async def test_handler(request):
        assert current_request_id() == request.headers.get(REQUEST_ID_HEADER)
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test with custom request ID
    test_id = str(uuid.uuid4())
    resp = await client.get("/", headers={REQUEST_ID_HEADER: test_id})
    assert resp.status == 200


async def test_request_id_middleware_without_request_id(aiohttp_client):
    async def test_handler(request):
        assert current_request_id() is not None
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test without request ID (should be None)
    resp = await client.get("/")
    assert resp.status == 200
