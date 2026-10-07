from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.api.gql_legacy.schema import graphene_schema
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData

ACT_AS_HEADER = "X-BackendAI-Act-As"

_SELF_QUERY = """
query {
    user { uuid email role }
    keypair { access_key }
}
"""


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    database_engine: ExtendedAsyncSAEngine,
) -> list[RouteRegistry]:
    """Serve the real graphene schema; the self queries only touch the DB."""
    gql_deps = MagicMock()
    gql_deps.config_provider = config_provider
    gql_deps.db = database_engine
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=graphene_schema,
                gql_deps=gql_deps,
                strawberry_schema=MagicMock(),
                public_strawberry_schema=MagicMock(),
            ),
            route_deps,
            sub_registries=[],
            gql_ws_handler=MagicMock(),
        ),
    ]


async def _query_self(
    registry: BackendAIClientRegistry, extra_headers: dict[str, str] | None = None
) -> dict[str, Any]:
    result = await registry._client._request(
        "POST",
        "/admin/gql",
        json={"query": _SELF_QUERY, "variables": {}},
        extra_headers=extra_headers,
    )
    response = cast(dict[str, Any], result)
    assert not response.get("errors"), f"Unexpected GQL errors: {response.get('errors')}"
    return cast(dict[str, Any], response["data"])


class TestLegacyGQLActAs:
    async def test_self_query_without_header_returns_caller(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        data = await _query_self(admin_registry)

        assert data["user"]["uuid"] == str(admin_user_fixture.user_uuid)
        assert data["keypair"]["access_key"] == admin_user_fixture.keypair.access_key

    async def test_self_query_acting_as_user_returns_target(
        self,
        admin_registry: BackendAIClientRegistry,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        data = await _query_self(
            admin_registry, {ACT_AS_HEADER: str(regular_user_fixture.user_uuid)}
        )

        assert data["user"]["uuid"] == str(regular_user_fixture.user_uuid)
        assert data["user"]["role"] == "user"
        assert data["keypair"]["access_key"] == regular_user_fixture.keypair.access_key
