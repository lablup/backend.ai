from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.ratelimit.handler import _rlim_window
from ai.backend.manager.api.rest.ratelimit.registry import register_ratelimit_routes
from ai.backend.manager.api.rest.types import RouteDeps

# TODO: These tests require a full Valkey rate-limit infrastructure
# (ValkeyRateLimitClient) that is not available through the current
# RouteDeps pattern.  They need to be refactored to inject a
# ValkeyRateLimitClient or to use a dedicated fixture.


@pytest.mark.skip(reason="Needs ValkeyRateLimitClient infrastructure")
async def test_check_rlim_for_anonymous_query(
    etcd_fixture: None,
    database_fixture: None,
    route_deps: RouteDeps,
    create_app_and_client: Any,
) -> None:
    mock_processors = MagicMock()
    app, client = await create_app_and_client(
        registries=[
            register_auth_routes(AuthHandler(processors=mock_processors), route_deps),
            register_ratelimit_routes(route_deps, valkey_rate_limit=None),
        ],
    )
    ret = await client.get("/")
    assert ret.status == 200
    assert ret.headers["X-RateLimit-Limit"] == "1000"
    assert ret.headers["X-RateLimit-Remaining"] == "1000"
    assert str(_rlim_window) == ret.headers["X-RateLimit-Window"]


@pytest.mark.skip(reason="Needs ValkeyRateLimitClient infrastructure")
async def test_check_rlim_for_authorized_query(
    etcd_fixture: None,
    database_fixture: None,
    route_deps: RouteDeps,
    create_app_and_client: Any,
    get_headers: Any,
) -> None:
    mock_processors = MagicMock()
    app, client = await create_app_and_client(
        registries=[
            register_auth_routes(AuthHandler(processors=mock_processors), route_deps),
            register_ratelimit_routes(route_deps, valkey_rate_limit=None),
        ],
    )
    url = "/auth/test"
    req_bytes = b'{"echo": "hello!"}'
    headers = get_headers("POST", url, req_bytes)
    ret = await client.post(url, data=req_bytes, headers=headers)

    assert ret.status == 200
    # The default example keypair's ratelimit is 30000.
    assert ret.headers["X-RateLimit-Limit"] == "30000"
    assert ret.headers["X-RateLimit-Remaining"] == "29999"
    assert str(_rlim_window) == ret.headers["X-RateLimit-Window"]
