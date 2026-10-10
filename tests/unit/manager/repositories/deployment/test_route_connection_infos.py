"""Tests for ``fetch_route_connection_infos`` against a real database.

The method reads the routes, keeps the ones whose session is RUNNING or
CREATING, then reads each session's main kernel and turns its first inference
port into an ``AppProxyRouteEntry``. It is the AppProxy routing table's only
source, so a row that silently drops here takes traffic with it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
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
from ai.backend.manager.data.kernel.types import KernelStatus
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
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
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
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields
from ai.backend.manager.models.routing.searchers import RouteInfoSearcher
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import TableOrORM, with_tables

# Tables the routes, sessions and kernels transitively need for their FK
# constraints. Only the rows the test reads are populated.
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

_KERNEL_HOST = "10.0.1.7"
_INFERENCE_PORT = 8081


@dataclass(frozen=True)
class _Environment:
    """The world the routes, sessions and kernels live in."""

    domain_name: str
    domain_id: DomainID
    resource_group_id: ResourceGroupID
    resource_group_name: str
    user_id: UUID
    access_key: AccessKey
    project_id: UUID
    endpoint_id: DeploymentID
    other_endpoint_id: DeploymentID
    revision_id: UUID


@dataclass(frozen=True)
class _Case:
    """One route and the session and main kernel behind it."""

    route_id: ReplicaID
    session_id: SessionId
    kernel_id: KernelId


class TestFetchRouteConnectionInfos:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, _REQUIRED_TABLES):
            yield database_connection

    @pytest.fixture
    def suffix(self) -> str:
        return uuid.uuid4().hex[:8]

    @pytest.fixture
    async def environment(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
    ) -> _Environment:
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"d-{suffix}"
        resource_group_id = ResourceGroupID(uuid.uuid4())
        resource_group_name = f"sg-{suffix}"
        user_id = uuid.uuid4()
        access_key = AccessKey(f"AK{suffix}"[:20].ljust(20, "X"))
        project_id = uuid.uuid4()
        endpoint_id = DeploymentID(uuid.uuid4())
        other_endpoint_id = DeploymentID(uuid.uuid4())
        revision_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    total_resource_slots=ResourceSlot(),
                )
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
            user_policy = UserResourcePolicyRow(
                name=f"up-{suffix}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            project_policy = ProjectResourcePolicyRow(
                name=f"pp-{suffix}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            keypair_policy = KeyPairResourcePolicyRow(
                name=f"kp-{suffix}",
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
            db_sess.add_all([user_policy, project_policy, keypair_policy])
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
                    domain_name=DomainName(domain_name),
                    domain_id=domain_id,
                    resource_policy=user_policy.name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"g-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy.name,
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user=user_id,
                    access_key=access_key,
                    secret_key=SecretValue("secret"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_policy.name,
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            for eid, name in (
                (endpoint_id, f"ep-{suffix}"),
                (other_endpoint_id, f"ep2-{suffix}"),
            ):
                db_sess.add(
                    EndpointRow(
                        id=eid,
                        name=name,
                        created_user=user_id,
                        session_owner=user_id,
                        domain=domain_name,
                        project=project_id,
                        resource_group=resource_group_name,
                        lifecycle_stage=EndpointLifecycle.CREATED,
                        replicas=1,
                    )
                )

        return _Environment(
            domain_name=domain_name,
            domain_id=domain_id,
            resource_group_id=resource_group_id,
            resource_group_name=resource_group_name,
            user_id=user_id,
            access_key=access_key,
            project_id=project_id,
            endpoint_id=endpoint_id,
            other_endpoint_id=other_endpoint_id,
            revision_id=revision_id,
        )

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

    def _searcher(self, *endpoint_ids: DeploymentID) -> RouteInfoSearcher:
        return RouteInfoSearcher(
            pagination=NoPagination(),
            conditions=[
                ReplicaSearchableFields.own.deployment_id.filter.in_(
                    UUIDInMatchSpec(values=[uuid.UUID(str(i)) for i in endpoint_ids], negated=False)
                )
            ],
        )

    async def _seed(
        self,
        db: ExtendedAsyncSAEngine,
        env: _Environment,
        *,
        endpoint_id: DeploymentID,
        session_status: SessionStatus = SessionStatus.RUNNING,
        kernel_host: str | None = _KERNEL_HOST,
        service_ports: list[dict[str, Any]] | None = None,
        cluster_role: str = "main",
        with_session: bool = True,
    ) -> _Case:
        """Insert one route, its session and one kernel of that session."""
        route_id = ReplicaID(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        now = datetime.now(tzutc())
        if service_ports is None:
            service_ports = [
                {"name": "inference", "is_inference": True, "host_ports": [_INFERENCE_PORT]}
            ]

        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=uuid.uuid4().hex,
                    name=f"s-{session_id.hex[:8]}",
                    session_type=SessionTypes.INFERENCE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_id=env.domain_id,
                    domain_name=env.domain_name,
                    group_id=env.project_id,
                    user_uuid=env.user_id,
                    access_key=env.access_key,
                    status=session_status,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=now,
                    vfolder_mounts=[],
                    use_host_network=False,
                    resource_group_id=env.resource_group_id,
                    scaling_group_name=env.resource_group_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    session_type=SessionTypes.INFERENCE,
                    domain_name=env.domain_name,
                    group_id=env.project_id,
                    user_uuid=env.user_id,
                    scaling_group=env.resource_group_name,
                    resource_group_id=env.resource_group_id,
                    access_key=env.access_key,
                    cluster_mode=ClusterMode.SINGLE_NODE.value,
                    cluster_size=1,
                    cluster_role=cluster_role,
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname=cluster_role,
                    image="cr.backend.ai/stable/python:latest",
                    architecture="x86_64",
                    registry="cr.backend.ai",
                    kernel_host=kernel_host,
                    service_ports=service_ports,
                    repl_in_port=2000,
                    repl_out_port=2001,
                    stdin_port=2002,
                    stdout_port=2003,
                    use_host_network=False,
                    status=KernelStatus.RUNNING,
                    status_history={},
                    status_changed=now,
                    result=SessionResult.UNDEFINED,
                    created_at=now,
                    occupied_shares={},
                    vfolder_mounts=[],
                    attached_devices={},
                )
            )
            await db_sess.flush()
            db_sess.add(
                RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=session_id if with_session else None,
                    session_owner=env.user_id,
                    domain=env.domain_name,
                    project=env.project_id,
                    status=RouteStatus.RUNNING,
                    sub_status=None,
                    health_status=RouteHealthStatus.HEALTHY,
                    traffic_status=RouteTrafficStatus.ACTIVE,
                    traffic_ratio=1.0,
                    revision=env.revision_id,
                )
            )

        return _Case(route_id=route_id, session_id=session_id, kernel_id=kernel_id)

    async def test_running_session_yields_one_entry_per_route(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
    ) -> None:
        """A route whose session is RUNNING carries its main kernel's host and
        first inference port, grouped under the route's endpoint."""
        case = await self._seed(db_with_cleanup, environment, endpoint_id=environment.endpoint_id)

        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id)
        )

        assert set(result.keys()) == {uuid.UUID(str(environment.endpoint_id))}
        (entry,) = result[uuid.UUID(str(environment.endpoint_id))]
        assert entry.session_id == case.session_id
        assert entry.route_id == case.route_id
        assert entry.kernel_host == _KERNEL_HOST
        assert entry.kernel_port == _INFERENCE_PORT

    async def test_entries_are_grouped_by_endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
    ) -> None:
        """Routes of two endpoints land under their own keys, and an endpoint
        with two routes keeps both."""
        first = await self._seed(db_with_cleanup, environment, endpoint_id=environment.endpoint_id)
        second = await self._seed(db_with_cleanup, environment, endpoint_id=environment.endpoint_id)
        other = await self._seed(
            db_with_cleanup, environment, endpoint_id=environment.other_endpoint_id
        )

        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id, environment.other_endpoint_id)
        )

        assert {route.route_id for route in result[uuid.UUID(str(environment.endpoint_id))]} == {
            first.route_id,
            second.route_id,
        }
        assert [
            route.route_id for route in result[uuid.UUID(str(environment.other_endpoint_id))]
        ] == [other.route_id]

    async def test_first_inference_port_wins(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
    ) -> None:
        """Among several inference ports the first one is taken, and a
        non-inference port ahead of it is skipped."""
        await self._seed(
            db_with_cleanup,
            environment,
            endpoint_id=environment.endpoint_id,
            service_ports=[
                {"name": "jupyter", "is_inference": False, "host_ports": [9999]},
                {"name": "infer-a", "is_inference": True, "host_ports": [7001, 7002]},
                {"name": "infer-b", "is_inference": True, "host_ports": [7003]},
            ],
        )

        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id)
        )

        (entry,) = result[uuid.UUID(str(environment.endpoint_id))]
        assert entry.kernel_port == 7001

    @pytest.mark.parametrize(
        ("reason", "kwargs"),
        [
            ("session not live", {"session_status": SessionStatus.TERMINATED}),
            ("session still pending", {"session_status": SessionStatus.PENDING}),
            ("kernel host not assigned", {"kernel_host": None}),
            ("no service ports", {"service_ports": []}),
            (
                "no inference port",
                {"service_ports": [{"name": "jupyter", "is_inference": False, "host_ports": [80]}]},
            ),
            (
                "inference port without host port",
                {"service_ports": [{"name": "infer", "is_inference": True, "host_ports": []}]},
            ),
            ("kernel is not the main one", {"cluster_role": "sub1"}),
            ("route names no session", {"with_session": False}),
        ],
    )
    async def test_route_is_skipped(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
        reason: str,
        kwargs: dict[str, Any],
    ) -> None:
        """A route contributes nothing when its session, its main kernel or that
        kernel's inference port is missing."""
        await self._seed(
            db_with_cleanup, environment, endpoint_id=environment.endpoint_id, **kwargs
        )

        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id)
        )

        assert result == {}, reason

    async def test_no_route_matches(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
    ) -> None:
        """An endpoint with no route at all answers with an empty mapping."""
        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id)
        )

        assert result == {}

    async def test_only_the_named_endpoints_are_read(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        environment: _Environment,
        repository: DeploymentRepository,
    ) -> None:
        """The searcher decides the scope: a route of another endpoint stays out."""
        await self._seed(db_with_cleanup, environment, endpoint_id=environment.other_endpoint_id)

        result = await repository.fetch_route_connection_infos(
            route_searcher=self._searcher(environment.endpoint_id)
        )

        assert result == {}
