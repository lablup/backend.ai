"""The revisions and the policy a deployment search fills in.

``search_legacy_endpoints`` fills them in the read ops of its search.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.endpoint.searchable_fields import DeploymentSearchableFields
from ai.backend.manager.models.endpoint.searchers import DeploymentInfoSearcher
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image.row import ImageRow
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
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.testutils.db import TableOrORM, with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

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
    ResourceSlotTypeRow,
    VFolderRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    DeploymentRevisionResourceSlotRow,
    EndpointRow,
    ReplicaGroupRow,
]


@dataclass(frozen=True)
class SeededDeployment:
    endpoint_id: DeploymentID
    current_revision_id: DeploymentRevisionID
    deploying_revision_id: DeploymentRevisionID


@dataclass(frozen=True)
class DeploymentSeeder:
    db: ExtendedAsyncSAEngine
    domain_name: DomainName
    resource_group: str
    user_id: uuid.UUID
    project_id: uuid.UUID
    image_id: ImageID
    runtime_variant_id: uuid.UUID

    async def seed(self, *, deploying_revision_exists: bool) -> SeededDeployment:
        """An endpoint whose primary group serves one revision while another deploys.

        With ``deploying_revision_exists=False`` the deploying id names no revision row.
        """
        endpoint_id = DeploymentID(uuid.uuid4())
        group_id = ReplicaGroupID(uuid.uuid4())
        current_id = DeploymentRevisionID(uuid.uuid4())
        deploying_id = DeploymentRevisionID(uuid.uuid4())
        async with self.db.begin_session() as db_sess:
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"ep-{uuid.uuid4().hex[:8]}",
                created_user=self.user_id,
                session_owner=self.user_id,
                domain=self.domain_name,
                project=self.project_id,
                resource_group=self.resource_group,
                url="http://test.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.READY,
                deploying_revision_id=deploying_id,
            )
            db_sess.add(endpoint)
            await db_sess.flush()
            db_sess.add(
                ReplicaGroupRow(
                    session_group_id=SessionGroupID(uuid.uuid4()),
                    id=group_id,
                    deployment_id=endpoint_id,
                    current_revision_id=current_id,
                    rollout=ReplicaGroupRolloutSpec(
                        max_surge=IntOrPercent(count=1),
                        max_unavailable=IntOrPercent(count=0),
                    ),
                )
            )
            endpoint.primary_replica_group_id = group_id
            db_sess.add(
                DeploymentPolicyRow(endpoint=endpoint_id, strategy=DeploymentStrategy.ROLLING)
            )
            revision_ids = [current_id, deploying_id] if deploying_revision_exists else [current_id]
            for number, revision_id in enumerate(revision_ids, start=1):
                db_sess.add(
                    DeploymentRevisionRow(
                        id=revision_id,
                        endpoint=endpoint_id,
                        revision_number=number,
                        image=self.image_id,
                        model=None,
                        model_mount_destination="/models",
                        resource_group=self.resource_group,
                        resource_opts={},
                        cluster_mode=ClusterMode.SINGLE_NODE.name,
                        cluster_size=1,
                        runtime_variant_id=self.runtime_variant_id,
                        environ={},
                        extra_mounts=[],
                    )
                )
        return SeededDeployment(
            endpoint_id=endpoint_id,
            current_revision_id=current_id,
            deploying_revision_id=deploying_id,
        )


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, _REQUIRED_TABLES):
        yield database_connection


@pytest.fixture
async def domain_fixture(db_with_cleanup: ExtendedAsyncSAEngine) -> DomainFixtureData:
    domain_id = DomainID(uuid.uuid4())
    name = f"d-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(DomainRow(id=domain_id, name=name, total_resource_slots=ResourceSlot()))
    return DomainFixtureData(domain_name=DomainName(name), domain_id=domain_id)


@pytest.fixture
async def resource_group_name(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
    name = f"sg-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            ResourceGroupRow(
                name=name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
    return name


@pytest.fixture
async def user_id(
    db_with_cleanup: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    user_uuid = uuid.uuid4()
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            UserResourcePolicyRow(
                name=f"up-{suffix}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await db_sess.flush()
        db_sess.add(
            UserRow(
                uuid=user_uuid,
                email=f"{suffix}@test.com",
                username=f"u-{suffix}",
                password=PasswordInfo(
                    password="x",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1,
                    salt_size=16,
                ),
                domain_id=domain_fixture.domain_id,
                domain_name=domain_fixture.domain_name,
                resource_policy=f"up-{suffix}",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
        )
    return user_uuid


@pytest.fixture
async def project_id(
    db_with_cleanup: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    project_uuid = uuid.uuid4()
    async with db_with_cleanup.begin_session() as db_sess:
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
            ProjectRow(
                id=project_uuid,
                name=f"g-{suffix}",
                domain_name=domain_fixture.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=f"pp-{suffix}",
            )
        )
    return project_uuid


@pytest.fixture
async def image_id(db_with_cleanup: ExtendedAsyncSAEngine) -> ImageID:
    suffix = uuid.uuid4().hex[:8]
    registry_uuid = uuid.uuid4()
    img_uuid = ImageID(uuid.uuid4())
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            ContainerRegistryRow(
                id=ContainerRegistryID(registry_uuid),
                url="https://test-registry.example.com",
                registry_name=f"reg-{suffix}",
                type=ContainerRegistryType.DOCKER,
                project=None,
                is_global=True,
            )
        )
        await db_sess.flush()
        image = ImageRow(
            name=f"reg-{suffix}/img:latest",
            project=None,
            architecture="x86_64",
            registry_id=registry_uuid,
            is_local=False,
            registry=f"reg-{suffix}",
            image="img",
            tag="latest",
            config_digest="sha256:" + "a" * 64,
            size_bytes=1_000_000,
            type=ImageType.COMPUTE,
            accelerators=None,
            labels={},
            resources={"cpu": {"min": "1"}, "mem": {"min": "1073741824"}},
        )
        image.id = img_uuid
        db_sess.add(image)
    return img_uuid


@pytest.fixture
async def runtime_variant_id(db_with_cleanup: ExtendedAsyncSAEngine) -> uuid.UUID:
    rv_uuid = uuid.uuid4()
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            RuntimeVariantRow(
                id=rv_uuid,
                name=f"rv-{uuid.uuid4().hex[:8]}",
                description="test",
                default_model_definition=DefaultModelDefinition(),
            )
        )
    return rv_uuid


@pytest.fixture
def seeder(
    db_with_cleanup: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    resource_group_name: str,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    image_id: ImageID,
    runtime_variant_id: uuid.UUID,
) -> DeploymentSeeder:
    return DeploymentSeeder(
        db=db_with_cleanup,
        domain_name=domain_fixture.domain_name,
        resource_group=resource_group_name,
        user_id=user_id,
        project_id=project_id,
        image_id=image_id,
        runtime_variant_id=runtime_variant_id,
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


class TestSearchLegacyEndpoints:
    async def _search(
        self, repository: DeploymentRepository, endpoint_id: DeploymentID
    ) -> DeploymentInfo:
        result = await repository.search_legacy_endpoints(
            DeploymentInfoSearcher(
                pagination=NoPagination(),
                conditions=[
                    DeploymentSearchableFields.own.entity_id.filter.equals(
                        UUIDEqualMatchSpec(value=endpoint_id, negated=False)
                    )
                ],
            )
        )
        (info,) = result.items
        return info

    async def test_fills_the_revisions_and_the_policy(
        self, deployment_repository: DeploymentRepository, seeder: DeploymentSeeder
    ) -> None:
        seeded = await seeder.seed(deploying_revision_exists=True)

        info = await self._search(deployment_repository, seeded.endpoint_id)

        assert info.current_revision is not None
        assert info.current_revision.id == seeded.current_revision_id
        assert info.deploying_revision is not None
        assert info.deploying_revision.id == seeded.deploying_revision_id
        assert info.policy is not None
        assert info.policy.strategy == DeploymentStrategy.ROLLING

    async def test_keeps_the_id_of_a_missing_revision(
        self, deployment_repository: DeploymentRepository, seeder: DeploymentSeeder
    ) -> None:
        seeded = await seeder.seed(deploying_revision_exists=False)

        info = await self._search(deployment_repository, seeded.endpoint_id)

        assert info.deploying_revision_id == seeded.deploying_revision_id
        assert info.deploying_revision is None
