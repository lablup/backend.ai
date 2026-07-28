"""Component test fixtures for prometheus query preset v2 search filters."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.prometheus_query_preset.handler import (
    V2PrometheusQueryPresetHandler,
)
from ai.backend.manager.api.rest.v2.prometheus_query_preset.registry import (
    register_v2_prometheus_query_preset_routes,
)
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.row import PresetOptions
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
    from tests.component.conftest import ServerInfo, UserFixtureData


@dataclass(frozen=True)
class PresetFilterDataset:
    """Seeded preset/category IDs for filter tests."""

    category_a_id: uuid.UUID
    category_b_id: uuid.UUID
    cpu_usage_id: uuid.UUID
    cpu_usage_name: str
    cpu_memory_id: uuid.UUID
    cpu_memory_name: str
    memory_usage_id: uuid.UUID
    memory_usage_name: str


@pytest.fixture()
def prometheus_client_mock() -> MagicMock:
    """Shared MagicMock(spec=PrometheusClient) — tests can stub query methods on it."""
    return MagicMock(spec=PrometheusClient)


@pytest.fixture()
def prometheus_query_preset_processors(
    database_engine: ExtendedAsyncSAEngine,
    prometheus_client_mock: MagicMock,
) -> PrometheusQueryPresetProcessors:
    repo = PrometheusQueryPresetRepository(database_engine, prometheus_client_mock)
    service = PrometheusQueryPresetService(
        repository=repo,
        prometheus_client=prometheus_client_mock,
        default_timewindow="5m",
    )
    return PrometheusQueryPresetProcessors(
        service=service,
        action_monitors=[],
        validators=MagicMock(spec=ActionValidators),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    prometheus_query_preset_processors: PrometheusQueryPresetProcessors,
) -> list[RouteRegistry]:
    processors = MagicMock(spec=Processors)
    processors.prometheus_query_preset = prometheus_query_preset_processors
    adapter = PrometheusQueryPresetAdapter(processors)
    handler = V2PrometheusQueryPresetHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_prometheus_query_preset_routes(handler, route_deps))
    return [v2_reg]


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
async def preset_filter_dataset(
    db_engine: SAEngine,
) -> AsyncIterator[PresetFilterDataset]:
    """Seed two categories and three presets for filter regression tests.

    Layout:
      - category_a: cpu_usage_*, cpu_memory_*
      - category_b: memory_usage_*

    Names carry a per-run hex suffix so concurrent test runs do not collide
    on the global preset table.
    """
    category_a_id = uuid.uuid4()
    category_b_id = uuid.uuid4()
    cpu_usage_id = uuid.uuid4()
    cpu_memory_id = uuid.uuid4()
    memory_usage_id = uuid.uuid4()
    cpu_usage_name = f"cpu_usage_{cpu_usage_id.hex[:8]}"
    cpu_memory_name = f"cpu_memory_{cpu_memory_id.hex[:8]}"
    memory_usage_name = f"memory_usage_{memory_usage_id.hex[:8]}"
    now = datetime.now(tz=UTC)
    options_value = PresetOptions(filter_labels=[], group_labels=[])

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(PrometheusQueryPresetCategoryRow.__table__).values([
                {
                    "id": category_a_id,
                    "name": f"cat-a-{category_a_id.hex[:8]}",
                    "description": None,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": category_b_id,
                    "name": f"cat-b-{category_b_id.hex[:8]}",
                    "description": None,
                    "created_at": now,
                    "updated_at": now,
                },
            ])
        )
        await conn.execute(
            sa.insert(PrometheusQueryPresetRow.__table__).values([
                {
                    "id": cpu_usage_id,
                    "name": cpu_usage_name,
                    "metric_name": "backendai_cpu",
                    "query_template": "avg({metric_name})",
                    "time_window": None,
                    "description": None,
                    "rank": 0,
                    "category_id": category_a_id,
                    "options": options_value,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": cpu_memory_id,
                    "name": cpu_memory_name,
                    "metric_name": "backendai_cpu_memory",
                    "query_template": "avg({metric_name})",
                    "time_window": None,
                    "description": None,
                    "rank": 0,
                    "category_id": category_a_id,
                    "options": options_value,
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": memory_usage_id,
                    "name": memory_usage_name,
                    "metric_name": "backendai_memory",
                    "query_template": "avg({metric_name})",
                    "time_window": None,
                    "description": None,
                    "rank": 0,
                    "category_id": category_b_id,
                    "options": options_value,
                    "created_at": now,
                    "updated_at": now,
                },
            ])
        )

    yield PresetFilterDataset(
        category_a_id=category_a_id,
        category_b_id=category_b_id,
        cpu_usage_id=cpu_usage_id,
        cpu_usage_name=cpu_usage_name,
        cpu_memory_id=cpu_memory_id,
        cpu_memory_name=cpu_memory_name,
        memory_usage_id=memory_usage_id,
        memory_usage_name=memory_usage_name,
    )

    preset_table = PrometheusQueryPresetRow.__table__
    category_table = PrometheusQueryPresetCategoryRow.__table__
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.delete(preset_table).where(
                preset_table.c.id.in_([cpu_usage_id, cpu_memory_id, memory_usage_id])
            )
        )
        await conn.execute(
            sa.delete(category_table).where(category_table.c.id.in_([category_a_id, category_b_id]))
        )
