"""Tests for search_deployments_in_project functionality in DeploymentRepository."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import EndpointId, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import DeploymentSummarySearchResult
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import ProjectDeploymentSearchScope
from ai.backend.testutils.db import with_tables


@dataclass
class TestData:
    project_a_id: uuid.UUID
    project_b_id: uuid.UUID
    endpoint_ids_in_a: list[uuid.UUID]
    endpoint_ids_in_b: list[uuid.UUID]


class TestEndpointSearchInProject:
    """Test cases for search_deployments_in_project in DeploymentRepository."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[TestData, None]:
        """Create two projects with endpoints: 2 in project A, 1 in project B."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-upolicy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-ppolicy-{uuid.uuid4().hex[:8]}"
        user_id = uuid.uuid4()
        project_a_id = uuid.uuid4()
        project_b_id = uuid.uuid4()
        registry_id = uuid.uuid4()
        image_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Domain
            db_sess.add(DomainRow(name=domain_name, total_resource_slots=ResourceSlot()))
            await db_sess.flush()

            # Scaling group
            db_sess.add(
                ScalingGroupRow(
                    name=sgroup_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await db_sess.flush()

            # Resource policies
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
            await db_sess.flush()

            # User
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    email=f"test-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"testuser-{uuid.uuid4().hex[:8]}",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1,
                        salt_size=16,
                    ),
                    domain_name=domain_name,
                    resource_policy=user_policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
            await db_sess.flush()

            # Two projects
            db_sess.add(
                GroupRow(
                    id=project_a_id,
                    name=f"project-a-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy_name,
                )
            )
            db_sess.add(
                GroupRow(
                    id=project_b_id,
                    name=f"project-b-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_policy_name,
                )
            )
            await db_sess.flush()

            # Container registry + image
            db_sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="http://test-registry.local",
                    registry_name=f"test-registry-{uuid.uuid4().hex[:8]}",
                    type=ContainerRegistryType.DOCKER,
                )
            )
            await db_sess.flush()

            image = ImageRow(
                name=f"test-image-{uuid.uuid4().hex[:8]}",
                project=None,
                image=f"test-image-{uuid.uuid4().hex[:8]}",
                tag="latest",
                registry=f"test-registry-{uuid.uuid4().hex[:8]}",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "a" * 64,
                size_bytes=1024,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1g"}},
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.flush()

            # Endpoints: 2 in project A, 1 in project B (all CREATED lifecycle)
            endpoint_ids_in_a: list[uuid.UUID] = []
            for i in range(2):
                eid = EndpointId(uuid.uuid4())
                db_sess.add(
                    EndpointRow(
                        id=eid,
                        name=f"endpoint-a-{i}-{uuid.uuid4().hex[:8]}",
                        created_user=user_id,
                        session_owner=user_id,
                        domain=domain_name,
                        project=project_a_id,
                        resource_group=sgroup_name,
                        lifecycle_stage=EndpointLifecycle.CREATED,
                        current_revision=uuid.uuid4(),
                        replicas=1,
                    )
                )
                endpoint_ids_in_a.append(eid)

            endpoint_ids_in_b: list[uuid.UUID] = []
            eid = EndpointId(uuid.uuid4())
            db_sess.add(
                EndpointRow(
                    id=eid,
                    name=f"endpoint-b-0-{uuid.uuid4().hex[:8]}",
                    created_user=user_id,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_b_id,
                    resource_group=sgroup_name,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                    current_revision=uuid.uuid4(),
                    replicas=1,
                )
            )
            endpoint_ids_in_b.append(eid)
            await db_sess.flush()

        yield TestData(
            project_a_id=project_a_id,
            project_b_id=project_b_id,
            endpoint_ids_in_a=endpoint_ids_in_a,
            endpoint_ids_in_b=endpoint_ids_in_b,
        )

    @pytest.fixture
    async def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        mock_storage_manager = AsyncMock()
        mock_valkey_stat = AsyncMock()
        mock_valkey_live = AsyncMock()
        mock_valkey_schedule = AsyncMock()
        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=mock_storage_manager,
            valkey_stat=mock_valkey_stat,
            valkey_live=mock_valkey_live,
            valkey_schedule=mock_valkey_schedule,
        )

    async def test_returns_only_endpoints_in_target_project(
        self,
        deployment_repository: DeploymentRepository,
        test_data: TestData,
    ) -> None:
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        scope = ProjectDeploymentSearchScope(project_id=test_data.project_a_id)

        result = await deployment_repository.search_deployments_in_project(querier, scope)

        assert isinstance(result, DeploymentSummarySearchResult)
        assert result.total_count == 2
        assert len(result.items) == 2
        returned_ids = {item.id for item in result.items}
        assert returned_ids == set(test_data.endpoint_ids_in_a)

    async def test_does_not_return_endpoints_from_other_project(
        self,
        deployment_repository: DeploymentRepository,
        test_data: TestData,
    ) -> None:
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        scope = ProjectDeploymentSearchScope(project_id=test_data.project_b_id)

        result = await deployment_repository.search_deployments_in_project(querier, scope)

        assert result.total_count == 1
        assert len(result.items) == 1
        returned_ids = {item.id for item in result.items}
        assert returned_ids == set(test_data.endpoint_ids_in_b)

    async def test_pagination_fields(
        self,
        deployment_repository: DeploymentRepository,
        test_data: TestData,
    ) -> None:
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        scope = ProjectDeploymentSearchScope(project_id=test_data.project_a_id)

        result = await deployment_repository.search_deployments_in_project(querier, scope)

        assert result.has_next_page is False
        assert result.has_previous_page is False
