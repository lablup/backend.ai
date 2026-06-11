import re

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from aiohttp.typedefs import Handler

from ai.backend.web.security import (
    SecurityPolicy,
    add_self_content_security_policy,
    csp_nonce_var,
    csp_policy_builder,
    reject_access_for_unsafe_file_policy,
    reject_metadata_local_link_policy,
    security_policy_middleware,
    set_content_type_nosniff_policy,
)

_NONCE_RE = re.compile(r"'nonce-([A-Za-z0-9_-]+)'")


@pytest.fixture
async def async_handler() -> Handler:
    async def handler(request: web.Request) -> web.Response:
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
async def test_reject_metadata_local_link_policy(
    async_handler: Handler, meta_local_link: str
) -> None:
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
async def test_reject_access_for_unsafe_file_policy(
    async_handler: Handler, url_suffix: str
) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[reject_access_for_unsafe_file_policy], response_policies=[]
    )
    request = make_mocked_request(
        "GET", f"/{url_suffix}", headers={"Host": "localhost"}, app=test_app
    )
    with pytest.raises(web.HTTPForbidden):
        await security_policy_middleware(request, async_handler)


async def test_add_self_content_security_policy(async_handler: Handler) -> None:
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


async def test_set_content_type_nosniff_policy(async_handler: Handler) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[], response_policies=[set_content_type_nosniff_policy]
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_csp_policy_injects_nonce_into_script_and_style_src(async_handler: Handler) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[],
        response_policies=[
            csp_policy_builder({
                "default-src": ["'self'"],
                "script-src": ["'self'"],
                "style-src": ["'self'", "'unsafe-inline'"],
            })
        ],
    )
    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    response = await security_policy_middleware(request, async_handler)

    csp = response.headers["Content-Security-Policy"]
    script_directive = next(d for d in csp.split(";") if d.strip().startswith("script-src"))
    style_directive = next(d for d in csp.split(";") if d.strip().startswith("style-src"))
    default_directive = next(d for d in csp.split(";") if d.strip().startswith("default-src"))

    script_nonce = _NONCE_RE.search(script_directive)
    style_nonce = _NONCE_RE.search(style_directive)
    assert script_nonce is not None
    assert style_nonce is not None
    # Same nonce is shared across directives within a single request.
    assert script_nonce.group(1) == style_nonce.group(1)
    # default-src is not a nonce-able directive, so it stays untouched.
    assert _NONCE_RE.search(default_directive) is None


async def test_csp_policy_uses_new_nonce_per_request(async_handler: Handler) -> None:
    test_app = web.Application()
    test_app["security_policy"] = SecurityPolicy(
        request_policies=[],
        response_policies=[csp_policy_builder({"script-src": ["'self'"]})],
    )

    def nonce_of(response: web.StreamResponse) -> str:
        match = _NONCE_RE.search(response.headers["Content-Security-Policy"])
        assert match is not None
        return match.group(1)

    request = make_mocked_request("GET", "/", headers={"Host": "localhost"}, app=test_app)
    first = nonce_of(await security_policy_middleware(request, async_handler))
    second = nonce_of(await security_policy_middleware(request, async_handler))

    assert first != second
    # The context variable is reset once the middleware returns.
    assert csp_nonce_var.get() == ""


def test_csp_policy_without_nonce_keeps_directives_clean() -> None:
    # Outside of the middleware no nonce is set, so none should be appended.
    policy = csp_policy_builder({"script-src": ["'self'"]})
    response = policy(web.Response())
    assert response.headers["Content-Security-Policy"] == "script-src 'self';"
