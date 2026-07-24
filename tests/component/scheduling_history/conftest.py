from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.replica_group_history import ReplicaGroupHistoryID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.adapters.scheduling_history.adapter import SchedulingHistoryAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.scheduling_history.handler import SchedulingHistoryHandler
from ai.backend.manager.api.rest.scheduling_history.registry import (
    register_scheduling_history_routes,
)
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.scheduling_history.handler import V2SchedulingHistoryHandler
from ai.backend.manager.api.rest.v2.scheduling_history.registry import (
    register_v2_scheduling_history_routes,
)
from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduling_history.repository import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


@pytest.fixture()
def scheduling_history_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> SchedulingHistoryProcessors:
    repo = SchedulingHistoryRepository(database_engine)
    service = SchedulingHistoryService(repo)
    return SchedulingHistoryProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(scope=AsyncMock(), single_entity=AsyncMock(), bulk=AsyncMock()),
        ),
    )


@pytest.fixture()
def scheduling_history_adapter(
    scheduling_history_processors: SchedulingHistoryProcessors,
) -> SchedulingHistoryAdapter:
    """Build an adapter wired only with scheduling-history processors."""
    processors = MagicMock()
    processors.scheduling_history = scheduling_history_processors
    return SchedulingHistoryAdapter(processors)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scheduling_history_processors: SchedulingHistoryProcessors,
    scheduling_history_adapter: SchedulingHistoryAdapter,
) -> list[RouteRegistry]:
    """Load both the v1 and v2 scheduling-history route trees."""
    v2_registry = RouteRegistry.create("v2", route_deps.cors_options)
    v2_registry.add_subregistry(
        register_v2_scheduling_history_routes(
            V2SchedulingHistoryHandler(adapter=scheduling_history_adapter),
            route_deps,
        )
    )
    return [
        register_scheduling_history_routes(
            SchedulingHistoryHandler(scheduling_history=scheduling_history_processors),
            route_deps,
        ),
        v2_registry,
    ]


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


@dataclass(frozen=True)
class _LifecycleRow:
    """One seeded lifecycle history row."""

    phase: str
    from_status: str
    to_status: str
    result: str
    attempts: int


@dataclass(frozen=True)
class ReplicaGroupHistorySeed:
    """Identifiers of the seeded deployment, replica groups, and their history rows."""

    deployment_id: DeploymentID
    replica_group_id: ReplicaGroupID
    other_replica_group_id: ReplicaGroupID
    lifecycle_history_ids: list[ReplicaGroupHistoryID]
    scaling_history_id: ReplicaGroupHistoryID
    other_group_history_id: ReplicaGroupHistoryID


@pytest.fixture()
async def replica_group_history_seed(
    database_engine: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    scaling_group_name: ResourceGroupName,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[ReplicaGroupHistorySeed]:
    """Seed one deployment with two replica groups so the scope has rows to exclude."""
    deployment_id = DeploymentID(uuid.uuid4())
    replica_group_id = ReplicaGroupID(uuid.uuid4())
    other_replica_group_id = ReplicaGroupID(uuid.uuid4())
    now = datetime.now(tz=UTC)
    rollout = ReplicaGroupRolloutSpec(
        max_surge=IntOrPercent(count=1),
        max_unavailable=IntOrPercent(count=0),
    )

    lifecycle_rows = [
        _LifecycleRow("DEPLOYING", "CREATED", "DEPLOYING", "SUCCESS", 1),
        _LifecycleRow("DEPLOYING", "DEPLOYING", "STABLE", "SUCCESS", 2),
        _LifecycleRow("DEPLOYING", "STABLE", "DEGRADED", "FAILURE", 3),
    ]
    lifecycle_history_ids = [ReplicaGroupHistoryID(uuid.uuid4()) for _ in lifecycle_rows]
    scaling_history_id = ReplicaGroupHistoryID(uuid.uuid4())
    other_group_history_id = ReplicaGroupHistoryID(uuid.uuid4())

    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            EndpointRow(
                id=deployment_id,
                name=f"endpoint-{deployment_id.hex[:8]}",
                created_user=admin_user_fixture.user_uuid,
                session_owner=admin_user_fixture.user_uuid,
                domain=domain_fixture.domain_name,
                project=group_fixture,
                resource_group=scaling_group_name,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=1,
            )
        )
        await db_sess.flush()
        db_sess.add_all([
            ReplicaGroupRow(id=gid, deployment_id=deployment_id, rollout=rollout)
            for gid in (replica_group_id, other_replica_group_id)
        ])
        await db_sess.flush()

        for offset, (hid, history_row) in enumerate(
            zip(lifecycle_history_ids, lifecycle_rows, strict=True)
        ):
            db_sess.add(
                ReplicaGroupHistoryRow(
                    id=hid,
                    replica_group_id=replica_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.LIFECYCLE,
                    phase=history_row.phase,
                    from_status=history_row.from_status,
                    to_status=history_row.to_status,
                    result=history_row.result,
                    error_code=(
                        None if history_row.result == "SUCCESS" else "ERR_REPLICA_GROUP_ROLLOUT"
                    ),
                    message=f"{history_row.phase} transition",
                    attempts=history_row.attempts,
                    created_at=now + timedelta(seconds=offset),
                    updated_at=now + timedelta(seconds=offset),
                )
            )
        db_sess.add_all([
            ReplicaGroupHistoryRow(
                id=scaling_history_id,
                replica_group_id=replica_group_id,
                deployment_id=deployment_id,
                category=ReplicaGroupHandlerCategory.SCALING,
                phase="SCALING_OUT",
                from_status="STABLE",
                to_status="SCALING_OUT",
                result="SUCCESS",
                error_code=None,
                message="scale out to 2 replicas",
                attempts=1,
                created_at=now + timedelta(seconds=len(lifecycle_rows)),
                updated_at=now + timedelta(seconds=len(lifecycle_rows)),
            ),
            ReplicaGroupHistoryRow(
                id=other_group_history_id,
                replica_group_id=other_replica_group_id,
                deployment_id=deployment_id,
                category=ReplicaGroupHandlerCategory.LIFECYCLE,
                phase="DEPLOYING",
                from_status="CREATED",
                to_status="DEPLOYING",
                result="SUCCESS",
                error_code=None,
                message="other group transition",
                attempts=1,
                created_at=now,
                updated_at=now,
            ),
        ])

    yield ReplicaGroupHistorySeed(
        deployment_id=deployment_id,
        replica_group_id=replica_group_id,
        other_replica_group_id=other_replica_group_id,
        lifecycle_history_ids=lifecycle_history_ids,
        scaling_history_id=scaling_history_id,
        other_group_history_id=other_group_history_id,
    )

    async with database_engine.begin() as conn:
        await conn.execute(
            sa.delete(ReplicaGroupHistoryRow).where(
                ReplicaGroupHistoryRow.deployment_id == deployment_id
            )
        )
        await conn.execute(
            sa.delete(ReplicaGroupRow).where(ReplicaGroupRow.deployment_id == deployment_id)
        )
        await conn.execute(sa.delete(EndpointRow).where(EndpointRow.id == deployment_id))
