"""Tests for ModelServingRepository.get_route_by_id."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
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
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
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


@dataclass(frozen=True)
class _Seed:
    endpoint_id: DeploymentID
    other_endpoint_id: DeploymentID
    route_id: ReplicaID


class TestGetRouteById:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, _REQUIRED_TABLES):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
        return ModelServingRepository(
            db=db_with_cleanup,
            v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
            permission_check=MagicMock(),
        )

    @pytest.fixture
    async def seed(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _Seed:
        """Two endpoints; one route belongs to the first."""
        suffix = uuid.uuid4().hex[:8]
        domain_name = f"d-{suffix}"
        domain_id = DomainID(uuid.uuid4())
        resource_group_name = f"sg-{suffix}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        endpoint_id = DeploymentID(uuid.uuid4())
        other_endpoint_id = DeploymentID(uuid.uuid4())
        route_id = ReplicaID(uuid.uuid4())

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(id=domain_id, name=domain_name, total_resource_slots=ResourceSlot())
            )
            db_sess.add(
                ResourceGroupRow(
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
            for ep_id in (endpoint_id, other_endpoint_id):
                db_sess.add(
                    EndpointRow(
                        id=ep_id,
                        name=f"ep-{ep_id.hex[:8]}",
                        created_user=user_id,
                        session_owner=user_id,
                        domain=domain_name,
                        project=project_id,
                        resource_group=resource_group_name,
                        lifecycle_stage=EndpointLifecycle.CREATED,
                        replicas=1,
                    )
                )
            await db_sess.flush()
            db_sess.add(
                RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_id,
                    status=RouteStatus.RUNNING,
                    health_status=RouteHealthStatus.HEALTHY,
                    traffic_status=RouteTrafficStatus.ACTIVE,
                    traffic_ratio=1.0,
                    revision=uuid.uuid4(),
                )
            )

        return _Seed(
            endpoint_id=endpoint_id,
            other_endpoint_id=other_endpoint_id,
            route_id=route_id,
        )

    async def test_returns_route_of_the_service(
        self,
        repository: ModelServingRepository,
        seed: _Seed,
    ) -> None:
        result = await repository.get_route_by_id(seed.route_id, seed.endpoint_id)

        assert result is not None
        assert result.id == seed.route_id
        assert result.endpoint == seed.endpoint_id
        assert result.status == RouteStatus.RUNNING

    async def test_returns_none_for_route_of_another_service(
        self,
        repository: ModelServingRepository,
        seed: _Seed,
    ) -> None:
        assert await repository.get_route_by_id(seed.route_id, seed.other_endpoint_id) is None

    async def test_returns_none_for_unknown_route(
        self,
        repository: ModelServingRepository,
        seed: _Seed,
    ) -> None:
        assert await repository.get_route_by_id(uuid.uuid4(), seed.endpoint_id) is None
