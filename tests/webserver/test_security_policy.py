import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.web.security import (
    SecurityPolicy,
    add_self_content_security_policy,
    reject_metadata_local_link,
    security_policy_middleware,
    set_content_type_nosniff,
)


@pytest.fixture
def default_app():
    app = web.Application(middlewares=[security_policy_middleware])
    app["security_policy"] = SecurityPolicy.default_policy()
    return app


@pytest.fixture
async def async_handler():
    async def handler(request):
        return web.Response()

    return handler


@pytest.fixture
def sync_handler():
    def handler(request):
        return web.Response()

    return handler


async def test_default_security_policy_reject_metadata_local_link(default_app, async_handler):
    request = make_mocked_request("GET", "/", headers={"Host": "169.254.169.254"}, app=default_app)
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, async_handler)


async def test_default_security_policy_response(default_app, async_handler):
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=default_app)
    response = await security_policy_middleware(request, async_handler)
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'self'; frame-ancestors 'none'"
    )
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_reject_metadata_local_link(async_handler):
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[reject_metadata_local_link], response_policies=[]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "169.254.169.254"}, app=test_app)
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, async_handler)


async def test_add_self_content_security_policy(async_handler):
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[], response_policies=[add_self_content_security_policy]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'self'; frame-ancestors 'none'"
    )


async def test_set_content_type_nosniff(async_handler):
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[], response_policies=[set_content_type_nosniff]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
