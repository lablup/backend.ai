import pytest
from aiohttp import web


@pytest.mark.asyncio
async def test_pipeline_login_proxy(aiohttp_client) -> None:
    app = web.Application()
    app.router.add_route("POST", "/pipeline/{path:.*login/$}", lambda request: web.Response())

    client = await aiohttp_client(app)

    response = await client.post("/pipeline/login/")
    assert response.status == 200

    response = await client.post("/pipeline/api/login/")
    assert response.status == 200
