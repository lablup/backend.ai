"""The routing-table entries the route connection read builds from routes, sessions and
their main kernels."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import AppProxyRouteEntry
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
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
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
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

_INFERENCE_PORT = 8000


@dataclass(frozen=True)
class _Place:
    """The rows every session and route of the test sits in."""

    domain_name: str
    domain_id: DomainID
    resource_group: str
    resource_group_id: UUID
    user_id: UUID
    project_id: UUID
    endpoint_id: DeploymentID


@dataclass(frozen=True)
class _Seeded:
    live_route_id: ReplicaID
    live_session_id: SessionId
    ended_route_id: ReplicaID


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, _REQUIRED_TABLES):
        yield database_connection


@pytest.fixture
async def place(db_with_cleanup: ExtendedAsyncSAEngine) -> _Place:
    suffix = uuid.uuid4().hex[:8]
    domain_id = DomainID(uuid.uuid4())
    domain_name = f"d-{suffix}"
    resource_group = f"sg-{suffix}"
    resource_group_id = uuid.uuid4()
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    endpoint_id = DeploymentID(uuid.uuid4())
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot()))
        db_sess.add(
            ResourceGroupRow(
                id=resource_group_id,
                name=resource_group,
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
                resource_group=resource_group,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=2,
            )
        )
    return _Place(
        domain_name=domain_name,
        domain_id=domain_id,
        resource_group=resource_group,
        resource_group_id=resource_group_id,
        user_id=user_id,
        project_id=project_id,
        endpoint_id=endpoint_id,
    )


def _session(place: _Place, session_id: SessionId, status: SessionStatus) -> SessionRow:
    return SessionRow(
        id=session_id,
        creation_id=session_id.hex[:32],
        name=f"s-{session_id.hex[:8]}",
        session_type=SessionTypes.INFERENCE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=2,
        domain_id=place.domain_id,
        domain_name=place.domain_name,
        group_id=place.project_id,
        user_uuid=place.user_id,
        access_key=AccessKey("AKIATEST"),
        status=status,
        status_history={},
        result=SessionResult.UNDEFINED,
        vfolder_mounts=[],
        use_host_network=False,
        resource_group_id=place.resource_group_id,
        scaling_group_name=place.resource_group,
    )


def _kernel(
    place: _Place,
    session_id: SessionId,
    *,
    cluster_role: str,
    host: str,
    service_ports: list[dict[str, Any]],
) -> KernelRow:
    return KernelRow(
        id=KernelId(uuid.uuid4()),
        session_id=session_id,
        session_type=SessionTypes.INFERENCE,
        domain_name=place.domain_name,
        group_id=place.project_id,
        user_uuid=place.user_id,
        access_key=AccessKey("AKIATEST"),
        cluster_mode=ClusterMode.SINGLE_NODE.value,
        cluster_size=2,
        cluster_role=cluster_role,
        cluster_idx=0 if cluster_role == DEFAULT_ROLE else 1,
        local_rank=0,
        cluster_hostname=cluster_role,
        scaling_group=place.resource_group,
        resource_group_id=place.resource_group_id,
        image="cr.backend.ai/stable/python:latest",
        architecture="x86_64",
        registry="cr.backend.ai",
        kernel_host=host,
        repl_in_port=2000,
        repl_out_port=2001,
        stdin_port=2002,
        stdout_port=2003,
        service_ports=service_ports,
        use_host_network=False,
        status=KernelStatus.RUNNING,
        status_history={},
        status_changed=datetime.now(UTC),
        result=SessionResult.UNDEFINED,
        occupied_shares={},
        vfolder_mounts=[],
        attached_devices={},
    )


def _route(place: _Place, route_id: ReplicaID, session_id: SessionId) -> RoutingRow:
    return RoutingRow(
        id=route_id,
        endpoint=place.endpoint_id,
        session=session_id,
        session_owner=place.user_id,
        domain=place.domain_name,
        project=place.project_id,
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_status=RouteTrafficStatus.ACTIVE,
        traffic_ratio=1.0,
        revision=uuid.uuid4(),
    )


def _inference_port(host_port: int) -> list[dict[str, Any]]:
    return [
        {
            "name": "inference",
            "is_inference": True,
            "protocol": "http",
            "container_ports": [_INFERENCE_PORT],
            "host_ports": [host_port],
        }
    ]


@pytest.fixture
async def seeded(db_with_cleanup: ExtendedAsyncSAEngine, place: _Place) -> _Seeded:
    """A live route whose session has a main and a sub kernel, and a route whose session
    has ended."""
    live_session = SessionId(uuid.uuid4())
    ended_session = SessionId(uuid.uuid4())
    live_route = ReplicaID(uuid.uuid4())
    ended_route = ReplicaID(uuid.uuid4())
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(_session(place, live_session, SessionStatus.RUNNING))
        db_sess.add(_session(place, ended_session, SessionStatus.TERMINATED))
        await db_sess.flush()
        db_sess.add(
            _kernel(
                place,
                live_session,
                cluster_role=DEFAULT_ROLE,
                host="10.0.0.1",
                service_ports=_inference_port(30001),
            )
        )
        db_sess.add(
            _kernel(
                place,
                live_session,
                cluster_role="sub",
                host="10.0.0.2",
                service_ports=_inference_port(30002),
            )
        )
        db_sess.add(
            _kernel(
                place,
                ended_session,
                cluster_role=DEFAULT_ROLE,
                host="10.0.0.3",
                service_ports=_inference_port(30003),
            )
        )
        await db_sess.flush()
        db_sess.add(_route(place, live_route, live_session))
        db_sess.add(_route(place, ended_route, ended_session))
    return _Seeded(
        live_route_id=live_route, live_session_id=live_session, ended_route_id=ended_route
    )


@pytest.fixture
def deployment_repository(db_with_cleanup: ExtendedAsyncSAEngine) -> DeploymentRepository:
    return DeploymentRepository(
        db=db_with_cleanup,
        reconcile_ops_provider=ReconcileOpsProvider(db_with_cleanup),
        storage_manager=AsyncMock(),
        valkey_stat=AsyncMock(),
        valkey_live=AsyncMock(),
        valkey_schedule=AsyncMock(),
        permission_check=AsyncMock(),
    )


class TestFetchRouteConnectionInfos:
    async def test_answers_the_main_kernel_of_each_live_route(
        self,
        deployment_repository: DeploymentRepository,
        place: _Place,
        seeded: _Seeded,
    ) -> None:
        """Only the main kernel's inference port is used, and a route whose session has
        ended is left out."""
        connection_infos = await deployment_repository.fetch_route_connection_infos(
            route_searcher=RouteInfoSearcher(
                pagination=NoPagination(),
                conditions=[
                    ReplicaSearchableFields.own.deployment_id.filter.in_(
                        UUIDInMatchSpec(values=[place.endpoint_id], negated=False)
                    )
                ],
            ),
        )

        assert connection_infos == {
            place.endpoint_id: [
                AppProxyRouteEntry(
                    session_id=seeded.live_session_id,
                    route_id=seeded.live_route_id,
                    kernel_host="10.0.0.1",
                    kernel_port=30001,
                )
            ]
        }
