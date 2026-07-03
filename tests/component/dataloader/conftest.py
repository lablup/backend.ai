"""Fixtures serving a test-only probe GQL schema through the real admin handler.

The probe field resolves through a real loader of the production ``DataLoaders``
class, backed by a mutable in-memory store instead of a domain/DB stack, so the
tests observe DataLoader caching behaviour itself without depending on any
entity domain and without exposing probe fields in the production schema.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest
import strawberry
from strawberry import Info
from strawberry.federation import Schema as StrawberrySchema

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps


@strawberry.type
class ProbeQuery:
    """Test-only query root exercising the per-request DataLoaders in the context."""

    @strawberry.field
    async def probe_cached_value(
        self,
        info: Info[StrawberryGQLContext],
        key: str,
    ) -> int:
        """Load the value for *key* through a real loader of the context's DataLoaders.

        Uses ``container_count_loader`` because it is the only loader returning a
        primitive value — the loader choice is irrelevant to the probe's semantics.
        """
        return await info.context.data_loaders.container_count_loader.load(AgentId(key))


@pytest.fixture()
def probe_schema() -> StrawberrySchema:
    """A minimal schema exposing only the probe field, served in place of the
    production strawberry schema."""
    return StrawberrySchema(query=ProbeQuery)


@pytest.fixture()
def loader_backing_store() -> dict[str, int]:
    """Mutable in-memory data source behind the probe loader.

    The test server runs in-process, so tests mutate this dict between requests
    to change what the loader's load_fn reads.
    """
    return {}


@pytest.fixture()
def probe_key() -> str:
    """A unique store key per test."""
    return f"probe-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def adapters_stub(loader_backing_store: dict[str, int]) -> MagicMock:
    """Adapters registry stub reading from the in-memory store.

    Raises ``KeyError`` for missing keys so tests can also observe that load
    failures are not cached across requests.
    """

    async def batch_load_container_counts(agent_ids: Sequence[AgentId]) -> list[int]:
        return [loader_backing_store[str(agent_id)] for agent_id in agent_ids]

    adapters = MagicMock()
    adapters.agent.batch_load_container_counts = batch_load_container_counts
    return adapters


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    probe_schema: StrawberrySchema,
    adapters_stub: MagicMock,
) -> list[RouteRegistry]:
    """Serve the probe schema through the real admin handler."""
    gql_deps = MagicMock()
    gql_deps.adapters = adapters_stub
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(),
                gql_deps=gql_deps,
                strawberry_schema=probe_schema,
                public_strawberry_schema=MagicMock(),
            ),
            route_deps,
            sub_registries=[],
            gql_ws_handler=MagicMock(),
        ),
    ]
