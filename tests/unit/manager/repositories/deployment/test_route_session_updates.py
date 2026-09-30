"""Tests for the session-lifecycle route updates on DeploymentRepository."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import TableOrORM, with_tables

_REQUIRED_TABLES: list[TableOrORM] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    EndpointRow,
    ResourcePresetRow,
    ReplicaGroupRow,
    RoutingRow,
]

_INITIAL_RETRIES = 2


@dataclass(frozen=True)
class _Seed:
    endpoint_id: DeploymentID
    session_id: SessionId
    session_route_id: ReplicaID
    failed_route_id: ReplicaID


class TestRouteSessionUpdates:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, _REQUIRED_TABLES):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DeploymentRepository:
        return DeploymentRepository(
            db=db_with_cleanup,
            reconcile_ops_provider=ReconcileOpsProvider(db_with_cleanup),
            storage_manager=AsyncMock(),
            valkey_stat=AsyncMock(),
            valkey_live=AsyncMock(),
            valkey_schedule=AsyncMock(),
            permission_check=AsyncMock(),
        )

    @pytest.fixture
    async def seed(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _Seed:
        """One endpoint (1 replica) with a RUNNING/HEALTHY route bound to an inference
        session and a sessionless FAILED_TO_START route."""
        suffix = uuid.uuid4().hex[:8]
        domain_name = f"d-{suffix}"
        domain_id = DomainID(uuid.uuid4())
        resource_group_id = ResourceGroupID(uuid.uuid4())
        resource_group_name = f"sg-{suffix}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        endpoint_id = DeploymentID(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        session_route_id = ReplicaID(uuid.uuid4())
        failed_route_id = ReplicaID(uuid.uuid4())
        revision_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=resource_group_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=f"up-{suffix}",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"pp-{suffix}",
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"{suffix}@test.com",
                    username=f"u-{suffix}",
                    password=PasswordInfo(
                        password="x",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_name=domain_name,
                    resource_policy=f"up-{suffix}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_id=domain_id,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"g-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=f"pp-{suffix}",
                )
            )
            await db_sess.flush()
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"ep-{suffix}",
                    created_user=user_id,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_id,
                    resource_group=resource_group_name,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                    replicas=1,
                    retries=_INITIAL_RETRIES,
                )
            )
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=str(session_id)[:32],
                    name=f"session-{suffix}",
                    session_type=SessionTypes.INFERENCE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_name=domain_name,
                    domain_id=domain_id,
                    resource_group_id=resource_group_id,
                    group_id=project_id,
                    user_uuid=user_id,
                    access_key=None,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    terminated_at=None,
                    starts_at=datetime(2026, 1, 1, tzinfo=UTC),
                    startup_command=None,
                    callback_url=None,
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    scaling_group_name=resource_group_name,
                )
            )
            await db_sess.flush()

            def _route(
                route_id: ReplicaID,
                session: SessionId | None,
                status: RouteStatus,
                health_status: RouteHealthStatus,
            ) -> RoutingRow:
                return RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=session,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_id,
                    status=status,
                    health_status=health_status,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                    traffic_ratio=1.0,
                    revision=revision_id,
                )

            db_sess.add_all([
                _route(
                    session_route_id, session_id, RouteStatus.RUNNING, RouteHealthStatus.HEALTHY
                ),
                _route(
                    failed_route_id,
                    None,
                    RouteStatus.FAILED_TO_START,
                    RouteHealthStatus.NOT_CHECKED,
                ),
            ])

        return _Seed(
            endpoint_id=endpoint_id,
            session_id=session_id,
            session_route_id=session_route_id,
            failed_route_id=failed_route_id,
        )

    @pytest.fixture
    async def unhealthy_seed(self, db_with_cleanup: ExtendedAsyncSAEngine, seed: _Seed) -> _Seed:
        """The seed with the session's route turned UNHEALTHY."""
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(RoutingRow)
                .where(RoutingRow.id == seed.session_route_id)
                .values(health_status=RouteHealthStatus.UNHEALTHY)
            )
        return seed

    async def _route(self, db: ExtendedAsyncSAEngine, route_id: ReplicaID) -> RoutingRow | None:
        async with db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(sa.select(RoutingRow).where(RoutingRow.id == route_id))
            return result.scalar_one_or_none()

    async def _retries(self, db: ExtendedAsyncSAEngine, endpoint_id: DeploymentID) -> int | None:
        async with db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(EndpointRow.retries).where(EndpointRow.id == endpoint_id)
            )
            return result.scalar_one_or_none()

    async def test_mark_route_failed_stores_error_and_bumps_retries(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seed: _Seed,
    ) -> None:
        error_data = {"type": "session_cancelled", "errors": [], "session_id": str(seed.session_id)}

        await repository.mark_route_failed_by_session(seed.session_id, error_data)

        route = await self._route(db_with_cleanup, seed.session_route_id)
        assert route is not None
        assert route.status == RouteStatus.FAILED_TO_START
        assert route.error_data == error_data
        assert await self._retries(db_with_cleanup, seed.endpoint_id) == _INITIAL_RETRIES + 1

    async def test_mark_route_failed_without_error_data_keeps_error_data(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seed: _Seed,
    ) -> None:
        await repository.mark_route_failed_by_session(seed.session_id, None)

        route = await self._route(db_with_cleanup, seed.session_route_id)
        assert route is not None
        assert route.status == RouteStatus.FAILED_TO_START
        assert not route.error_data
        assert await self._retries(db_with_cleanup, seed.endpoint_id) == _INITIAL_RETRIES + 1

    async def test_mark_route_failed_ignores_session_without_route(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seed: _Seed,
    ) -> None:
        await repository.mark_route_failed_by_session(SessionId(uuid.uuid4()), None)

        route = await self._route(db_with_cleanup, seed.session_route_id)
        assert route is not None
        assert route.status == RouteStatus.RUNNING
        assert await self._retries(db_with_cleanup, seed.endpoint_id) == _INITIAL_RETRIES

    async def test_clear_errors_when_all_replicas_healthy(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seed: _Seed,
    ) -> None:
        await repository.clear_endpoint_errors_by_session(seed.session_id)

        assert await self._retries(db_with_cleanup, seed.endpoint_id) == 0
        assert await self._route(db_with_cleanup, seed.failed_route_id) is None
        assert await self._route(db_with_cleanup, seed.session_route_id) is not None

    async def test_clear_errors_skipped_when_replicas_not_healthy(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        unhealthy_seed: _Seed,
    ) -> None:
        await repository.clear_endpoint_errors_by_session(unhealthy_seed.session_id)

        assert await self._retries(db_with_cleanup, unhealthy_seed.endpoint_id) == _INITIAL_RETRIES
        assert await self._route(db_with_cleanup, unhealthy_seed.failed_route_id) is not None

    async def test_clear_errors_ignores_session_without_route(
        self,
        repository: DeploymentRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seed: _Seed,
    ) -> None:
        await repository.clear_endpoint_errors_by_session(SessionId(uuid.uuid4()))

        assert await self._retries(db_with_cleanup, seed.endpoint_id) == _INITIAL_RETRIES
        assert await self._route(db_with_cleanup, seed.failed_route_id) is not None
