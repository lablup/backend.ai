"""Integration tests for sessions.replica_id population on route binding.

BA-6267: ``DeploymentDBSource.update_route_sessions`` binds a route to a session
and mirrors that binding onto ``sessions.replica_id`` (the replica the session
serves). Contract under test:

1. Binding a route sets the route's ``session`` *and* the session's ``replica_id``.
2. First-bind-wins: a session that already carries a ``replica_id`` is not
   overwritten when another route later binds to it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.deployment.db_source.db_source import DeploymentDBSource
from ai.backend.testutils.db import with_tables

# Tables `RoutingRow` / `SessionRow` transitively require for their FK
# constraints. We only populate the handful of rows the test routes/sessions need.
_REQUIRED_TABLES = [
    DomainRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    GroupRow,
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
    RoutingRow,
]


@dataclass(frozen=True)
class _Env:
    domain: str
    scaling_group: str
    user_id: UUID
    project_id: UUID
    access_key: AccessKey
    endpoint_id: DeploymentID
    revision_id: UUID


class TestUpdateRouteSessionsReplicaId:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, _REQUIRED_TABLES):
            yield database_connection

    @pytest.fixture
    def db_source(self, db: ExtendedAsyncSAEngine) -> DeploymentDBSource:
        return DeploymentDBSource(
            db=db,
            storage_manager=MagicMock(spec=StorageSessionManager),
        )

    @pytest.fixture
    async def env(self, db: ExtendedAsyncSAEngine) -> _Env:
        suffix = uuid.uuid4().hex[:8]
        domain = f"d-{suffix}"
        scaling_group = f"sg-{suffix}"
        user_policy = f"up-{suffix}"
        project_policy = f"pp-{suffix}"
        kp_policy = f"kp-{suffix}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        access_key = AccessKey(f"AK{suffix}")
        revision_id = uuid.uuid4()

        async with db.begin_session() as sess:
            sess.add(DomainRow(name=domain, total_resource_slots=ResourceSlot()))
            sess.add(
                ScalingGroupRow(
                    name=scaling_group,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"u-{suffix}",
                    email=f"{suffix}@test.io",
                    domain_name=domain,
                    role=UserRole.USER,
                    resource_policy=user_policy,
                )
            )
            sess.add(
                GroupRow(
                    id=project_id,
                    name=f"g-{suffix}",
                    domain_name=domain,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key="secret",
                    user=user_id,
                    is_active=True,
                    resource_policy=kp_policy,
                )
            )
            await sess.flush()

        endpoint_id = await self._make_endpoint(
            db, domain, scaling_group, user_id, project_id, suffix
        )
        return _Env(
            domain=domain,
            scaling_group=scaling_group,
            user_id=user_id,
            project_id=project_id,
            access_key=access_key,
            endpoint_id=endpoint_id,
            revision_id=revision_id,
        )

    async def _make_endpoint(
        self,
        db: ExtendedAsyncSAEngine,
        domain: str,
        scaling_group: str,
        user_id: UUID,
        project_id: UUID,
        suffix: str,
    ) -> DeploymentID:
        endpoint_id = DeploymentID(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"ep-{suffix}-{uuid.uuid4().hex[:6]}",
                    created_user=user_id,
                    session_owner=user_id,
                    domain=domain,
                    project=project_id,
                    resource_group=scaling_group,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                    replicas=1,
                )
            )
        return endpoint_id

    async def _make_session(self, db: ExtendedAsyncSAEngine, env: _Env) -> SessionId:
        session_id = SessionId(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                SessionRow(
                    id=session_id,
                    name=f"s-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INFERENCE,
                    domain_name=env.domain,
                    group_id=env.project_id,
                    user_uuid=env.user_id,
                    access_key=env.access_key,
                    scaling_group_name=env.scaling_group,
                    status=SessionStatus.RUNNING,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                    created_at=datetime.now(tzutc()),
                    images=["python:3.11"],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
        return session_id

    async def _make_route(
        self,
        db: ExtendedAsyncSAEngine,
        env: _Env,
        endpoint_id: DeploymentID,
    ) -> ReplicaID:
        route_id = ReplicaID(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=env.user_id,
                    domain=env.domain,
                    project=env.project_id,
                    status=RouteStatus.PROVISIONING,
                    health_status=RouteHealthStatus.NOT_CHECKED,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                    traffic_ratio=1.0,
                    revision=env.revision_id,
                )
            )
        return route_id

    async def _replica_id(self, db: ExtendedAsyncSAEngine, session_id: SessionId) -> UUID | None:
        async with db.begin_readonly_session() as sess:
            return await sess.scalar(
                sa.select(SessionRow.replica_id).where(SessionRow.id == session_id)
            )

    async def _route_session(self, db: ExtendedAsyncSAEngine, route_id: ReplicaID) -> UUID | None:
        async with db.begin_readonly_session() as sess:
            return await sess.scalar(sa.select(RoutingRow.session).where(RoutingRow.id == route_id))

    async def test_binds_route_and_sets_replica_id(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: DeploymentDBSource,
        env: _Env,
    ) -> None:
        session_id = await self._make_session(db, env)
        route_id = await self._make_route(db, env, env.endpoint_id)

        await db_source.update_route_sessions({route_id: session_id})

        assert await self._route_session(db, route_id) == session_id
        assert await self._replica_id(db, session_id) == route_id

    async def test_first_bind_wins_does_not_overwrite(
        self,
        db: ExtendedAsyncSAEngine,
        db_source: DeploymentDBSource,
        env: _Env,
    ) -> None:
        session_id = await self._make_session(db, env)
        first_route = await self._make_route(db, env, env.endpoint_id)
        await db_source.update_route_sessions({first_route: session_id})
        assert await self._replica_id(db, session_id) == first_route

        # A second route (distinct endpoint, so the (endpoint, session) uniqueness
        # holds) binds to the same session later. The session's replica_id must
        # keep pointing at the first route.
        other_endpoint = await self._make_endpoint(
            db, env.domain, env.scaling_group, env.user_id, env.project_id, "x"
        )
        second_route = await self._make_route(db, env, other_endpoint)
        await db_source.update_route_sessions({second_route: session_id})

        assert await self._route_session(db, second_route) == session_id
        assert await self._replica_id(db, session_id) == first_route
