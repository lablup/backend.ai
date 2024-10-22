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
def app(security_policy):
    app = web.Application(middlewares=[security_policy_middleware])
    app["security_policy"] = security_policy
    return app


async def test_default_security_policy_reject_metadata_local_link(_):
    test_app = app(SecurityPolicy.default_policy())
    request = make_mocked_request("GET", "/", headers={"Host": "169.254.169.254"}, app=test_app)
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, lambda r: web.Response())


async def test_default_security_policy_response(_):
    test_app = app(SecurityPolicy.default_policy())
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, lambda r: web.Response())
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'self'; frame-ancestors 'none'"
    )
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_reject_metadata_local_link(_):
    test_app = app(SecurityPolicy(request_policies=[reject_metadata_local_link]))
    request = make_mocked_request("GET", "/", headers={"Host": "169.254.169.254"}, app=test_app)
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, lambda r: web.Response())


async def test_add_self_content_security_policy(_):
    test_app = app(SecurityPolicy(response_policies=[add_self_content_security_policy]))
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, lambda r: web.Response())
    assert (
        response.headers["Content-Security-Policy"] == "default-src 'self'; frame-ancestors 'none'"
    )


async def test_set_content_type_nosniff(_):
    test_app = app(SecurityPolicy(response_policies=[set_content_type_nosniff]))
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, lambda r: web.Response())
    assert response.headers["X-Content-Type-Options"] == "nosniff"
