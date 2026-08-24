"""Component test fixtures for the client IP masking policies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.client_ip_masking import CLIENT_IP_MASKING_POLICY_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.client_ip_masking.handler import V2ClientIPMaskingHandler
from ai.backend.manager.api.rest.v2.client_ip_masking.registry import (
    register_v2_client_ip_masking_routes,
)
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.client_ip_masking.repository import ClientIPMaskingRepository
from ai.backend.manager.services.client_ip_masking.processors import ClientIPMaskingProcessors
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


@pytest.fixture()
def client_ip_masking_processors(
    processor_registry: ProcessorRegistry[Any],
) -> ClientIPMaskingProcessors:
    return ClientIPMaskingProcessors(
        processor_registry.group(GroupMeta(CLIENT_IP_MASKING_POLICY_ENTITY_TYPE))
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    client_ip_masking_processors: ClientIPMaskingProcessors,
) -> list[RouteRegistry]:
    processors = MagicMock(spec=Processors)
    processors.client_ip_masking = client_ip_masking_processors
    adapter = ClientIPMaskingAdapter(processors)
    handler = V2ClientIPMaskingHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_client_ip_masking_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
def masking_repository(database_engine: ExtendedAsyncSAEngine) -> ClientIPMaskingRepository:
    """The read the login path resolves its masking through."""
    return ClientIPMaskingRepository(database_engine)


@pytest.fixture(autouse=True)
async def clean_policies(database_engine: ExtendedAsyncSAEngine) -> AsyncIterator[None]:
    """Empty the table around each test.

    The policies are global, so a row one test leaves behind would decide what the
    next one resolves.
    """
    async with database_engine.begin() as conn:
        await conn.execute(sa.delete(ClientIPMaskingPolicyRow.__table__))
    yield
    async with database_engine.begin() as conn:
        await conn.execute(sa.delete(ClientIPMaskingPolicyRow.__table__))


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
