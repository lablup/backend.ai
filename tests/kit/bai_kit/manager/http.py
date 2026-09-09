"""The HTTP runner: the same scenario, through an aiohttp server and the client SDK v2.

Starts a server that mounts only the wired domain's v2 routes, signs each step as the
persona's keypair, and reads the answer back through ``V2ClientRegistry``. An expected
manager exception is checked by HTTP status: the class carries it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any, cast, override
from unittest.mock import MagicMock

import pytest
import yarl
from aiohttp import web

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_STATISTICS_DB
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget
from ai.backend.manager.api.rest.app import api_middleware, mount_registries
from ai.backend.manager.api.rest.middleware import (
    build_auth_middleware,
    build_exception_middleware,
    client_ip_middleware,
    request_id_middleware,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import (
    ALL_ALLOWED,
    READ_ALLOWED,
    server_status_required,
)
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.scenario import (
    Call,
    Persona,
    Raises,
    Scenario,
    Step,
    StepContext,
    check_then,
)
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.personas import SUPERADMIN
from bai_kit.manager.runner import AdapterRunner, Wired, Wiring
from bai_kit.manager.world import World

Routes = Callable[[Any, RouteDeps], RouteRegistry]


@asynccontextmanager
async def serve(
    wired: Wired,
    routes: Routes,
    config_provider: ManagerConfigProvider,
    engine: ExtendedAsyncSAEngine,
    redis_addr: HostPortPairModel,
) -> AsyncIterator[yarl.URL]:
    etcd = MagicMock(spec=AsyncEtcd)
    valkey_stat = await ValkeyStatClient.create(
        ValkeyTarget(addr=f"{redis_addr.host}:{redis_addr.port}"),
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="kit_stat",
    )
    app = web.Application(
        middlewares=[
            request_id_middleware,
            client_ip_middleware,
            build_exception_middleware(
                error_monitor=ErrorPluginContext(etcd, {}),
                stats_monitor=StatsPluginContext(etcd, {}),
                config_provider=config_provider,
            ),
            build_auth_middleware(
                db=engine,
                key_provider_pool=KeyProviderPool(
                    providers=[], write_provider_type=KeyProviderType.PLAIN
                ),
                jwt_validator=MagicMock(),
                valkey_stat=valkey_stat,
                hook_plugin_ctx=HookPluginContext(etcd, {}),
            ),
            api_middleware,
        ]
    )
    route_deps = RouteDeps(
        cors_options={},
        read_status_mw=server_status_required(READ_ALLOWED, config_provider),
        all_status_mw=server_status_required(ALL_ALLOWED, config_provider),
    )
    v2 = RouteRegistry.create("v2", {})
    v2.add_subregistry(routes(wired.adapter, route_deps))
    mount_registries(app, [v2])

    runner = web.AppRunner(app, handle_signals=False)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        # Port 0 means the OS picks one; the socket is where the chosen number is.
        sockets = cast(Any, site._server).sockets
        port = sockets[0].getsockname()[1]
        yield yarl.URL(f"http://127.0.0.1:{port}")
    finally:
        await runner.cleanup()
        await valkey_stat.close()


class HttpRunner(AdapterRunner):
    """``AdapterRunner`` with the call replaced by an SDK v2 round trip."""

    name = "http"

    def __init__(
        self,
        wiring: Wiring,
        engine: ExtendedAsyncSAEngine,
        world: World,
        base_config: Mapping[str, Any],
        recorder: ActionRecorder,
        redis_addr: HostPortPairModel,
        routes: Routes,
        default_actor: Persona = SUPERADMIN,
    ) -> None:
        super().__init__(wiring, engine, world, base_config, recorder, default_actor)
        self._redis_addr = redis_addr
        self._routes = routes

    @override
    async def __call__(self, scenario: Scenario) -> None:
        wired, config_provider = self.assemble(scenario)
        ctx = StepContext()
        await self.seed(scenario, ctx)
        async with serve(
            wired, self._routes, config_provider, self._engine, self._redis_addr
        ) as endpoint:
            for step in scenario.all_steps(self.name):
                await self._run_http_step(scenario, step, ctx, wired, endpoint)

    async def _client_for(self, endpoint: yarl.URL, actor: Persona) -> V2ClientRegistry:
        seeded = self._world.users[actor]
        return await V2ClientRegistry.create(
            ClientConfig(endpoint=endpoint),
            HMACAuth(access_key=seeded.access_key, secret_key=seeded.secret_key),
        )

    async def _run_http_step(
        self,
        scenario: Scenario,
        step: Step,
        ctx: StepContext,
        wired: Wired,
        endpoint: yarl.URL,
    ) -> None:
        actor = step.actor or scenario.actor or self._default_actor
        when = self.resolve_when(step, ctx)
        if isinstance(when, Call):
            name, args, kwargs = when.method, when.args, dict(when.kwargs)
        else:
            dispatched = wired.dispatch.get(type(when))
            if dispatched is None:
                raise KeyError(f"no SDK method for {type(when).__name__}; name it with Call(...)")
            name, args, kwargs = dispatched, (when,), {}
        registry = await self._client_for(endpoint, actor)
        try:
            client = getattr(registry, wired.client_attr)
            method = getattr(client, name, None)
            if method is None:
                pytest.skip(f"SDK v2 {type(client).__name__} has no {name}()")
            try:
                result = await method(*args, **kwargs)
            except BackendAPIError as e:
                self._check_http_error(step, e, scenario.id)
                ctx.results.append(e)
                return
        finally:
            await registry.close()
        check_then(step.then, result, scenario.id, wired.extras)
        ctx.results.append(result)

    def _check_http_error(self, step: Step, error: BackendAPIError, scenario_id: str) -> None:
        if not isinstance(step.then, Raises):
            raise error
        expected_status = getattr(step.then.exc_type, "status_code", None)
        if expected_status is None:
            raise AssertionError(
                f"[{scenario_id}] {step.then.exc_type.__name__} carries no HTTP status; "
                "the HTTP runner cannot map it"
            ) from error
        if error.status != expected_status:
            raise AssertionError(
                f"[{scenario_id}] expected HTTP {expected_status} "
                f"({step.then.exc_type.__name__}), got {error.status}: {error}"
            ) from error


def http_runner(
    module: Any,
    world_template: Any,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
    redis_container: tuple[str, HostPortPairModel],
) -> HttpRunner:
    """Build the HTTP runner for a test module that declares ``WIRING`` and ``ROUTES``.
    Called from a fixture the module defines, so adapter-only modules never import the
    REST layer's closure."""
    _, redis_addr = redis_container
    return HttpRunner(
        wiring=module.WIRING,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, redis_addr),
        recorder=recorder,
        redis_addr=redis_addr,
        routes=module.ROUTES,
    )
