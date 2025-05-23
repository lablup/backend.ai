import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.typedefs import Handler

from ai.backend.web.security import (
    SecurityPolicy,
    add_self_content_security_policy,
    reject_access_for_unsafe_file_policy,
    reject_metadata_local_link_policy,
    security_policy_middleware,
    set_content_type_nosniff_policy,
)


@pytest.fixture
async def async_handler() -> Handler:
    async def handler(request):
        return web.Response()

    return handler


@pytest.mark.parametrize(
    "meta_local_link",
    [
        "metadata.google.internal",
        "169.254.169.254",
        "100.100.100.200",
        "alibaba.zaproxy.org",
        "metadata.oraclecloud.com",
    ],
)
async def test_reject_metadata_local_link_policy(async_handler, meta_local_link) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[reject_metadata_local_link_policy], response_policies=[]
    )
    request = make_mocked_request("GET", "/", headers={"Host": meta_local_link}, app=test_app)
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, async_handler)


@pytest.mark.parametrize(
    "url_suffix",
    [
        "._darcs",
        ".bzr",
        ".hg",
        "BitKeeper",
        ".bak",
        ".log",
        ".git",
        ".svn",
    ],
)
async def test_reject_access_for_unsafe_file_policy(async_handler, url_suffix) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[reject_access_for_unsafe_file_policy], response_policies=[]
    )
    request = make_mocked_request(
        "GET", f"/{url_suffix}", headers={"Host": "localhost"}, app=test_app
    )
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, async_handler)


async def test_add_self_content_security_policy(async_handler) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[], response_policies=[add_self_content_security_policy]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)
    assert (
        response.headers["Content-Security-Policy"]
        == "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; form-action 'self';"
    )


async def test_set_content_type_nosniff_policy(async_handler) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[], response_policies=[set_content_type_nosniff_policy]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
