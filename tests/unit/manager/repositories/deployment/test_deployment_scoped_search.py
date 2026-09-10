"""The project and user deployment scopes on the modern endpoint search."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
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
from ai.backend.manager.models.endpoint.scopes import (
    ProjectDeploymentOperationScope,
    UserDeploymentOperationScope,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass
class TestData:
    owner_id: uuid.UUID
    other_user_id: uuid.UUID
    project_a_id: uuid.UUID
    project_b_id: uuid.UUID
    endpoint_ids_in_a: list[uuid.UUID]
    endpoint_ids_in_b: list[uuid.UUID]


def _user_row(user_id: uuid.UUID, domain_id: DomainID, domain_name: str, policy: str) -> UserRow:
    return UserRow(
        uuid=user_id,
        email=f"test-{uuid.uuid4().hex[:8]}@test.com",
        username=f"testuser-{uuid.uuid4().hex[:8]}",
        password=PasswordInfo(
            password="test_password",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=1,
            salt_size=16,
        ),
        domain_id=domain_id,
        domain_name=domain_name,
        resource_policy=policy,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )


class TestDeploymentScopedSearch:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                VirtualEntityRow,
                EntityMembershipRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[TestData, None]:
        """One owner with 2 endpoints in project A and 1 in project B; one user with none."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        domain_id = DomainID(uuid.uuid4())
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-upolicy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-ppolicy-{uuid.uuid4().hex[:8]}"
        owner_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        project_a_id = uuid.uuid4()
        project_b_id = uuid.uuid4()
        registry_id = uuid.uuid4()
        image_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    total_resource_slots=ResourceSlot(),
                )
            )
            await db_sess.flush()

            db_sess.add(
                ResourceGroupRow(
                    name=sgroup_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            await db_sess.flush()

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

            db_sess.add(_user_row(owner_id, domain_id, domain_name, user_policy_name))
            db_sess.add(_user_row(other_user_id, domain_id, domain_name, user_policy_name))
            await db_sess.flush()

            for project_id, label in ((project_a_id, "a"), (project_b_id, "b")):
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=f"project-{label}-{uuid.uuid4().hex[:8]}",
                        domain_name=domain_name,
                        total_resource_slots=ResourceSlot(),
                        resource_policy=project_policy_name,
                    )
                )
            await db_sess.flush()

            db_sess.add(
                ContainerRegistryRow(
                    id=ContainerRegistryID(registry_id),
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
            image.id = ImageID(image_id)
            db_sess.add(image)
            await db_sess.flush()

            endpoint_ids_in_a: list[uuid.UUID] = []
            endpoint_ids_in_b: list[uuid.UUID] = []
            for project_id, ids, count in (
                (project_a_id, endpoint_ids_in_a, 2),
                (project_b_id, endpoint_ids_in_b, 1),
            ):
                for i in range(count):
                    eid = DeploymentID(uuid.uuid4())
                    db_sess.add(
                        EndpointRow(
                            id=eid,
                            name=f"endpoint-{i}-{uuid.uuid4().hex[:8]}",
                            created_user=owner_id,
                            session_owner=owner_id,
                            domain=domain_name,
                            project=project_id,
                            resource_group=sgroup_name,
                            lifecycle_stage=EndpointLifecycle.CREATED,
                            replicas=1,
                        )
                    )
                    ids.append(eid)
            await db_sess.flush()

        yield TestData(
            owner_id=owner_id,
            other_user_id=other_user_id,
            project_a_id=project_a_id,
            project_b_id=project_b_id,
            endpoint_ids_in_a=endpoint_ids_in_a,
            endpoint_ids_in_b=endpoint_ids_in_b,
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
        )

    @pytest.fixture
    def querier(self) -> BatchQuerier:
        return BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

    async def test_project_scope_returns_only_that_project(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        result = await repository.search_endpoints_in_scopes(
            querier, [ProjectDeploymentOperationScope(project_id=test_data.project_a_id)]
        )

        assert result.total_count == 2
        assert {item.id for item in result.items} == set(test_data.endpoint_ids_in_a)
        assert result.has_next_page is False
        assert result.has_previous_page is False

    async def test_project_scope_reads_the_modern_info(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        result = await repository.search_endpoints_in_scopes(
            querier, [ProjectDeploymentOperationScope(project_id=test_data.project_b_id)]
        )

        (item,) = result.items
        assert isinstance(item, DeploymentInfo)
        assert item.metadata.project == test_data.project_b_id
        assert item.metadata.created_user == test_data.owner_id
        assert item.state.lifecycle == EndpointLifecycle.CREATED
        assert item.current_revision_id is None
        assert item.policy is None

    async def test_user_scope_returns_the_deployments_the_user_created(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        result = await repository.search_endpoints_in_scopes(
            querier, [UserDeploymentOperationScope(user_id=test_data.owner_id)]
        )

        assert result.total_count == 3
        assert {item.id for item in result.items} == set(
            test_data.endpoint_ids_in_a + test_data.endpoint_ids_in_b
        )

    async def test_user_scope_is_empty_for_a_user_who_created_none(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        result = await repository.search_endpoints_in_scopes(
            querier, [UserDeploymentOperationScope(user_id=test_data.other_user_id)]
        )

        assert result.total_count == 0
        assert result.items == []

    async def test_unknown_project_is_refused(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        with pytest.raises(ProjectNotFound):
            await repository.search_endpoints_in_scopes(
                querier, [ProjectDeploymentOperationScope(project_id=uuid.uuid4())]
            )

    async def test_unknown_user_is_refused(
        self,
        repository: DeploymentRepository,
        querier: BatchQuerier,
        test_data: TestData,
    ) -> None:
        with pytest.raises(UserNotFound):
            await repository.search_endpoints_in_scopes(
                querier, [UserDeploymentOperationScope(user_id=uuid.uuid4())]
            )
