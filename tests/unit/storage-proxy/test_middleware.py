import aiohttp
import pytest
from aiohttp import web

from ai.backend.storage.api.manager import token_auth_middleware


class TestStorageManagerAPIMiddleware:
    @pytest.mark.asyncio
    async def test_auth_token_middleware_return_json_body_response(self, aiohttp_client) -> None:
        async def handler(request):
            return web.Response(text="OK")

        app = web.Application(middlewares=[token_auth_middleware])
        url = "/test"
        app.router.add_get(url, handler)
        client = await aiohttp_client(app)

        resp: aiohttp.ClientResponse = await client.get(url)
        assert resp.status == 403
        assert resp.content_type == "application/problem+json"

        # Verify the response body is a valid JSON, not raising parsing errors
        data = await resp.json()
        assert data is not None
