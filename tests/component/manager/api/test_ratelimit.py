from typing import Any

import pytest

from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.ratelimit.handler import _rlim_window
from ai.backend.manager.api.rest.ratelimit.registry import register_ratelimit_routes
from ai.backend.manager.api.rest.types import ModuleDeps

# TODO: These tests require a full Valkey rate-limit infrastructure
# (ValkeyRateLimitClient) that is not available through the new ModuleDeps
# pattern.  They need to be refactored to inject a ValkeyRateLimitClient
# into ModuleDeps or to use a dedicated fixture.


@pytest.mark.skip(reason="Needs ValkeyRateLimitClient infrastructure via ModuleDeps")
async def test_check_rlim_for_anonymous_query(
    etcd_fixture: None,
    database_fixture: None,
    server_module_deps: ModuleDeps,
    create_app_and_client: Any,
) -> None:
    app, client = await create_app_and_client(
        module_deps=server_module_deps,
        registrars=[register_auth_routes, register_ratelimit_routes],
    )
    ret = await client.get("/")
    assert ret.status == 200
    assert ret.headers["X-RateLimit-Limit"] == "1000"
    assert ret.headers["X-RateLimit-Remaining"] == "1000"
    assert str(_rlim_window) == ret.headers["X-RateLimit-Window"]


@pytest.mark.skip(reason="Needs ValkeyRateLimitClient infrastructure via ModuleDeps")
async def test_check_rlim_for_authorized_query(
    etcd_fixture: None,
    database_fixture: None,
    server_module_deps: ModuleDeps,
    create_app_and_client: Any,
    get_headers: Any,
) -> None:
    app, client = await create_app_and_client(
        module_deps=server_module_deps,
        registrars=[register_auth_routes, register_ratelimit_routes],
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
