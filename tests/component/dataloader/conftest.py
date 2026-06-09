from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from strawberry.federation import Schema as StrawberrySchema

from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.schema import schema as strawberry_schema
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider


@pytest.fixture()
def gql_schema() -> StrawberrySchema:
    """The real Strawberry (v2) GraphQL schema served at /admin/gql/strawberry."""
    return strawberry_schema


@pytest.fixture()
def data_loaders() -> DataLoaders:
    """The single DataLoaders instance shared across all requests of the test app.

    The probe barrier forces the two concurrent probe requests to issue their loads
    in the same event-loop tick, so they deterministically coalesce into one batch.
    Its party count must match the number of concurrent requests per test (2 here).
    """
    loaders = DataLoaders(MagicMock())
    loaders.probe_barrier = asyncio.Barrier(2)
    return loaders


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    gql_schema: StrawberrySchema,
    data_loaders: DataLoaders,
) -> list[RouteRegistry]:
    """Serve the real strawberry schema with a real config provider and DataLoaders."""
    mock_gql_deps = MagicMock()
    # GQLValidationExtension reads introspection / max-depth from the config provider.
    mock_gql_deps.config_provider = config_provider
    # The probe resolver loads via this shared DataLoaders instance.
    mock_gql_deps.strawberry_data_loaders = data_loaders
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=mock_gql_deps,
                strawberry_schema=gql_schema,
            ),
            route_deps,
            sub_registries=[],
            gql_ws_handler=MagicMock(),
        ),
    ]
