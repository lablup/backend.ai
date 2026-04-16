"""Component test fixtures for v2 Prometheus Query Preset GET endpoint RBAC validation."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleStatus,
    ScopeType,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.prometheus_query_preset import (
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
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
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
class PresetFixtureData:
    id: uuid.UUID
    name: str
    metric_name: str
    query_template: str


PresetFactory = Callable[..., Coroutine[Any, Any, PresetFixtureData]]


# ---------------------------------------------------------------------------
# Real infrastructure fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def rbac_permission_repo(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerRepository:
    """Real permission controller repository backed by real DB."""
    return PermissionControllerRepository(database_engine)


@pytest.fixture()
def preset_repository(
    database_engine: ExtendedAsyncSAEngine,
) -> PrometheusQueryPresetRepository:
    """Real prometheus query preset repository backed by real DB."""
    return PrometheusQueryPresetRepository(database_engine)


@pytest.fixture()
def preset_service(
    preset_repository: PrometheusQueryPresetRepository,
) -> PrometheusQueryPresetService:
    """Real service with real repository, mock prometheus client (external dep)."""
    return PrometheusQueryPresetService(
        repository=preset_repository,
        prometheus_client=MagicMock(),
        default_timewindow="1m",
    )


@pytest.fixture()
def preset_processors(
    preset_service: PrometheusQueryPresetService,
    rbac_permission_repo: PermissionControllerRepository,
) -> PrometheusQueryPresetProcessors:
    """Real processors with a real SingleEntityActionRBACValidator.

    Single-entity RBAC checks use check_permission_with_scope_chain() against
    the real DB. In this test setup, that means GET access without explicit
    RBAC permission grants is denied for non-superadmins.
    """
    real_single_entity_validator = SingleEntityActionRBACValidator(rbac_permission_repo)
    return PrometheusQueryPresetProcessors(
        preset_service,
        [],
        ActionValidators(
            rbac=RBACValidators(
                scope=AsyncMock(),
                single_entity=real_single_entity_validator,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Server + route fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    preset_processors: PrometheusQueryPresetProcessors,
) -> list[RouteRegistry]:
    """Register v2 prometheus query preset routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.prometheus_query_preset = preset_processors
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
    """V2 client registry authenticated as superadmin."""
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
    """V2 client registry authenticated as a regular (non-admin) user."""
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


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def preset_factory(
    db_engine: SAEngine,
) -> AsyncIterator[PresetFactory]:
    """Factory that inserts preset rows directly into DB."""
    table = PrometheusQueryPresetRow.__table__
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> PresetFixtureData:
        unique = secrets.token_hex(4)
        preset_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": preset_id,
            "name": f"test-preset-{unique}",
            "metric_name": f"test_metric_{unique}",
            "query_template": "rate(test_metric[{{window}}])",
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(table.insert().values(**defaults))
        created_ids.append(defaults["id"])
        return PresetFixtureData(
            id=defaults["id"],
            name=defaults["name"],
            metric_name=defaults["metric_name"],
            query_template=defaults["query_template"],
        )

    yield _create

    async with db_engine.begin() as conn:
        for pid in reversed(created_ids):
            await conn.execute(table.delete().where(table.c.id == pid))


@pytest.fixture()
async def preset_a(
    preset_factory: PresetFactory,
) -> PresetFixtureData:
    """Pre-created preset (no ownership semantics — used across RBAC scenarios)."""
    return await preset_factory()


@pytest.fixture()
async def preset_b(
    preset_factory: PresetFactory,
) -> PresetFixtureData:
    """Pre-created preset (no ownership semantics — used across RBAC scenarios)."""
    return await preset_factory()


@pytest.fixture()
async def preset_c(
    preset_factory: PresetFactory,
) -> PresetFixtureData:
    """Pre-created preset (no ownership semantics — used across RBAC scenarios)."""
    return await preset_factory()


# ---------------------------------------------------------------------------
# RBAC permission grant fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
async def grant_user_read_on_preset(
    db_engine: SAEngine,
    regular_user_fixture: UserFixtureData,
    preset_a: PresetFixtureData,
) -> AsyncIterator[None]:
    """Grant the regular user READ permission on ``preset_a``.

    Creates a role + permission + user_role assignment, then cleans up after
    the test.
    """
    role_id = uuid.uuid4()
    permission_id = uuid.uuid4()
    user_role_id = uuid.uuid4()

    role_table = RoleRow.__table__
    perm_table = PermissionRow.__table__
    user_role_table = UserRoleRow.__table__

    async with db_engine.begin() as conn:
        await conn.execute(
            role_table.insert().values(
                id=role_id,
                name=f"test-read-preset-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
            )
        )
        await conn.execute(
            perm_table.insert().values(
                id=permission_id,
                role_id=role_id,
                scope_type=ScopeType.PROMETHEUS_QUERY_PRESET,
                scope_id=str(preset_a.id),
                entity_type=EntityType.PROMETHEUS_QUERY_PRESET,
                operation=OperationType.READ,
            )
        )
        await conn.execute(
            user_role_table.insert().values(
                id=user_role_id,
                user_id=regular_user_fixture.user_uuid,
                role_id=role_id,
            )
        )

    yield

    async with db_engine.begin() as conn:
        await conn.execute(
            user_role_table.delete().where(
                sa.column("id") == user_role_id,
            )
        )
        await conn.execute(
            perm_table.delete().where(
                sa.column("id") == permission_id,
            )
        )
        await conn.execute(
            role_table.delete().where(
                sa.column("id") == role_id,
            )
        )
