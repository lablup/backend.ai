import json
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.defs import REDIS_RATE_LIMIT_DB, RedisRole
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.ratelimit.handler import _rlim_window
from ai.backend.manager.api.rest.ratelimit.registry import register_ratelimit_routes
from ai.backend.manager.api.rest.types import ModuleDeps
from ai.backend.manager.server import (
    agent_registry_ctx,
    database_ctx,
    event_dispatcher_plugin_ctx,
    event_hub_ctx,
    event_producer_ctx,
    hook_plugin_ctx,
    message_queue_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    redis_ctx,
    repositories_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.processors import Processors


@asynccontextmanager
async def rate_limit_valkey_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Create a ValkeyRateLimitClient for component tests."""
    client = await ValkeyRateLimitClient.create(
        root_ctx.valkey_profile_target.profile_target(RedisRole.RATE_LIMIT),
        db_id=REDIS_RATE_LIMIT_DB,
        human_readable_name="ratelimit",
    )
    root_ctx.valkey_rate_limit = client  # type: ignore[attr-defined]
    try:
        yield
    finally:
        await client.close()


@pytest.fixture()
def server_module_deps_factory() -> Callable[[RootContext], ModuleDeps]:
    """Override to include valkey_rate_limit for ratelimit tests."""

    def _factory(root_ctx: RootContext) -> ModuleDeps:
        return ModuleDeps(
            cors_options=root_ctx.cors_options,
            processors=cast(Processors, getattr(root_ctx, "processors", None) or MagicMock()),
            config_provider=root_ctx.config_provider,
            gql_context_deps=MagicMock(),
            valkey_rate_limit=getattr(root_ctx, "valkey_rate_limit", None),
        )

    return _factory


async def test_check_rlim_for_anonymous_query(
    etcd_fixture: None,
    mock_etcd_ctx: Any,
    mock_config_provider_ctx: Any,
    database_fixture: None,
    create_app_and_client: Any,
) -> None:
    app, client = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            redis_ctx,
            rate_limit_valkey_ctx,
            database_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            event_dispatcher_plugin_ctx,
            agent_registry_ctx,
        ],
        [register_auth_routes, register_ratelimit_routes],
    )
    ret = await client.get("/")
    assert ret.status == 200
    assert ret.headers["X-RateLimit-Limit"] == "1000"
    assert ret.headers["X-RateLimit-Remaining"] == "1000"
    assert str(_rlim_window) == ret.headers["X-RateLimit-Window"]


async def test_check_rlim_for_authorized_query(
    etcd_fixture: None,
    mock_etcd_ctx: Any,
    mock_config_provider_ctx: Any,
    database_fixture: None,
    create_app_and_client: Any,
    get_headers: Any,
) -> None:
    app, client = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            redis_ctx,
            rate_limit_valkey_ctx,
            database_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            event_dispatcher_plugin_ctx,
            agent_registry_ctx,
        ],
        [register_auth_routes, register_ratelimit_routes],
    )
    url = "/auth/test"
    req_bytes = json.dumps({"echo": "hello!"}).encode()
    headers = get_headers("POST", url, req_bytes)
    ret = await client.post(url, data=req_bytes, headers=headers)

    assert ret.status == 200
    # The default example keypair's ratelimit is 30000.
    assert ret.headers["X-RateLimit-Limit"] == "30000"
    assert ret.headers["X-RateLimit-Remaining"] == "29999"
    assert str(_rlim_window) == ret.headers["X-RateLimit-Window"]
