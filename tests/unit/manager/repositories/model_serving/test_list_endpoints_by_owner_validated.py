"""
Regression test for issue #11372 (expanded scope):
``ModelServingRepository.list_endpoints_by_owner_validated`` must drive
``EndpointRow.to_data()`` end-to-end without raising ``MissingGreenlet``.

The latent crash path is ``ModelServingService.list_serve``, which projects
each returned ``EndpointData`` and reads ``endpoint.routings`` plus the
revision-derived fields. ``_to_endpoint_datas`` reads the active revision,
the creator and owner emails and the routings with their own queries and
builds ``EndpointData`` from them, so nothing lazy-loads inside the async
transaction. ``search_services_paginated`` lists the same owned endpoint.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.config import DefaultModelDefinition, ModelDefinition
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_serving.types import EndpointData, EndpointLifecycle
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.endpoint.searchers import DeploymentInfoSearcher
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
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
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Provision the table set ``list_endpoints_by_owner_validated`` exercises."""
    async with with_tables(
        database_connection,
        [
            DomainRow,
            ResourceGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            ProjectRow,
            ContainerRegistryRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
            DeploymentPolicyRow,
            ReplicaGroupRow,
            RuntimeVariantRow,
            DeploymentRevisionPresetRow,
            DeploymentRevisionRow,
            ResourceSlotTypeRow,
            DeploymentRevisionResourceSlotRow,
            SessionRow,
            RoutingRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def test_domain(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> DomainFixtureData:
    domain_id = DomainID(uuid.uuid4())
    name = f"test-domain-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            DomainRow(
                id=domain_id,
                name=name,
                total_resource_slots=ResourceSlot(),
            )
        )
        await sess.flush()
    return DomainFixtureData(domain_name=DomainName(name), domain_id=domain_id)


@pytest.fixture
async def test_scaling_group(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
    name = f"test-sg-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            ResourceGroupRow(
                name=name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ResourceGroupOpts(),
            )
        )
        await sess.flush()
    return name


@pytest.fixture
async def test_user(
    db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
) -> tuple[uuid.UUID, str]:
    user_id = uuid.uuid4()
    email = f"test-{uuid.uuid4().hex[:8]}@test.com"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            UserResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=user_id,
                email=email,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                password=PasswordInfo(
                    password="pw",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1,
                    salt_size=16,
                ),
                domain_id=test_domain.domain_id,
                domain_name=test_domain.domain_name,
                resource_policy="default",
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
            )
        )
        await sess.flush()
        sess.add(
            KeyPairResourcePolicyRow(
                name="default",
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
        )
        await sess.flush()
        sess.add(
            KeyPairRow(
                access_key="TESTKEY",
                secret_key=SecretValue("TESTSECRET"),
                is_active=True,
                is_admin=True,
                user=user_id,
                resource_policy="default",
                is_default=True,
            )
        )
        await sess.flush()
        await sess.flush()
    return user_id, email


@pytest.fixture
async def test_creator_user(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_user: tuple[uuid.UUID, str],
) -> tuple[uuid.UUID, str]:
    """A user who created the endpoint, kept apart from its owner."""
    user_id = uuid.uuid4()
    email = f"creator-{uuid.uuid4().hex[:8]}@test.com"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            UserRow(
                uuid=user_id,
                email=email,
                username=f"creator-{uuid.uuid4().hex[:8]}",
                password=PasswordInfo(
                    password="pw",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1,
                    salt_size=16,
                ),
                domain_id=test_domain.domain_id,
                domain_name=test_domain.domain_name,
                resource_policy="default",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
        )
        await sess.flush()
    return user_id, email


@pytest.fixture
async def test_group_id(
    db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
) -> uuid.UUID:
    group_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            ProjectResourcePolicyRow(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        await sess.flush()
        sess.add(
            ProjectRow(
                id=group_id,
                name=f"test-grp-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy="default",
            )
        )
        await sess.flush()
    return group_id


@pytest.fixture
async def test_image_id(db_with_cleanup: ExtendedAsyncSAEngine) -> uuid.UUID:
    image_id = uuid.uuid4()
    registry_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            ContainerRegistryRow(
                id=ContainerRegistryID(registry_id),
                url="http://test.local",
                registry_name=f"test-reg-{uuid.uuid4().hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
        await sess.flush()
        image = ImageRow(
            name=f"test-img-{uuid.uuid4().hex[:8]}",
            project=None,
            image=f"test-img:{uuid.uuid4().hex[:8]}",
            tag="latest",
            registry=f"test-reg-{uuid.uuid4().hex[:8]}",
            registry_id=registry_id,
            architecture="aarch64",
            config_digest="sha256:" + "a" * 64,
            size_bytes=1024,
            type=ImageType.COMPUTE,
            labels={},
            resources={"cpu": {"min": "1"}, "mem": {"min": "64m"}},
        )
        image.id = ImageID(image_id)
        sess.add(image)
        await sess.flush()
    return image_id


@pytest.fixture
async def listed_endpoint(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_user: tuple[uuid.UUID, str],
    test_creator_user: tuple[uuid.UUID, str],
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_scaling_group: str,
    test_image_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    """Create a CREATED endpoint with one revision (current) and one route
    so ``list_endpoints_by_owner_validated`` returns it. Returns
    ``(endpoint_id, endpoint_name)``.
    """
    user_id, _email = test_user
    creator_id, _creator_email = test_creator_user
    endpoint_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    route_id = uuid.uuid4()
    runtime_variant_id = uuid.uuid4()
    endpoint_name = f"test-ep-{uuid.uuid4().hex[:8]}"

    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            EndpointRow(
                id=endpoint_id,
                name=endpoint_name,
                created_user=creator_id,
                session_owner=user_id,
                domain=test_domain.domain_name,
                project=test_group_id,
                resource_group=test_scaling_group,
                # ``list_endpoints_by_owner_validated`` filters by CREATED.
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=1,
            )
        )
        await sess.flush()

        sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
        sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
        sess.add(
            RuntimeVariantRow(
                id=runtime_variant_id,
                name=f"variant-{runtime_variant_id.hex[:8]}",
                description="test variant",
                default_model_definition=DefaultModelDefinition(models=[]),
            )
        )
        await sess.flush()

        sess.add(
            DeploymentRevisionRow(
                id=revision_id,
                endpoint=endpoint_id,
                revision_number=1,
                image=test_image_id,
                model_mount_destination="/models",
                model_definition_path="model-definition.yaml",
                model_definition=ModelDefinition.model_validate({"models": []}),
                resource_group=test_scaling_group,
                resource_opts={},
                cluster_mode="single-node",
                cluster_size=1,
                environ={},
                runtime_variant_id=runtime_variant_id,
                extra_mounts=[],
            )
        )
        await sess.flush()

        sess.add(
            DeploymentRevisionResourceSlotRow(
                revision_id=revision_id,
                slot_name="cpu",
                quantity="1",
            )
        )
        sess.add(
            DeploymentRevisionResourceSlotRow(
                revision_id=revision_id,
                slot_name="mem",
                quantity="268435456",
            )
        )
        await sess.flush()

        # Current revision lives on the primary replica group.
        group_id = uuid.uuid4()
        sess.add(
            ReplicaGroupRow(
                session_group_id=SessionGroupID(uuid.uuid4()),
                id=ReplicaGroupID(group_id),
                deployment_id=DeploymentID(endpoint_id),
                current_revision_id=revision_id,
                rollout=ReplicaGroupRolloutSpec(
                    max_surge=IntOrPercent(count=1),
                    max_unavailable=IntOrPercent(count=0),
                ),
            )
        )
        await sess.flush()
        await sess.execute(
            sa.update(EndpointRow)
            .where(EndpointRow.id == endpoint_id)
            .values(primary_replica_group_id=group_id)
        )
        await sess.flush()

        sess.add(
            RoutingRow(
                id=route_id,
                endpoint=DeploymentID(endpoint_id),
                session=None,
                status=RouteStatus.RUNNING,
                traffic_ratio=1.0,
                session_owner=user_id,
                domain=test_domain.domain_name,
                project=test_group_id,
                revision=revision_id,
            )
        )
        await sess.flush()

    return endpoint_id, endpoint_name


@pytest.fixture
def repository(db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
    return ModelServingRepository(
        db=db_with_cleanup,
        v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
        permission_check=MagicMock(),
    )


async def test_list_endpoints_by_owner_validated_drives_to_data_end_to_end(
    repository: ModelServingRepository,
    test_user: tuple[uuid.UUID, str],
    test_creator_user: tuple[uuid.UUID, str],
    listed_endpoint: tuple[uuid.UUID, str],
) -> None:
    """``list_endpoints_by_owner_validated`` returns ``EndpointData`` with the
    creator and owner emails, the routings and the revision-derived fields
    filled from the separate reads in ``_to_endpoint_datas``.
    """
    user_id, owner_email = test_user
    _creator_id, creator_email = test_creator_user
    endpoint_id, endpoint_name = listed_endpoint

    results = await repository.list_endpoints_by_owner_validated(user_id)

    assert len(results) == 1
    endpoint = results[0]
    assert isinstance(endpoint, EndpointData)
    assert endpoint.id == endpoint_id
    assert endpoint.name == endpoint_name
    # session_owner -> its user's email; "" when no user row matches.
    assert endpoint.session_owner_email == owner_email
    # created_user -> its user's email; None when no user row matches.
    assert endpoint.created_user_email == creator_email
    # The active revision's image.
    assert endpoint.image is not None
    # The routings read by endpoint id.
    assert len(endpoint.routings) == 1


async def test_search_services_paginated_reads_the_current_revision_slots(
    repository: ModelServingRepository,
    test_user: tuple[uuid.UUID, str],
    listed_endpoint: tuple[uuid.UUID, str],
) -> None:
    """The resource slots come from the current revision, read in the search's read ops."""
    user_id, _owner_email = test_user
    endpoint_id, _endpoint_name = listed_endpoint

    result = await repository.search_services_paginated(
        user_id, DeploymentInfoSearcher(pagination=NoPagination())
    )

    (item,) = result.items
    assert item.id == endpoint_id
    assert item.resource_slots == ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("268435456")})
    assert len(item.routings) == 1


@pytest.fixture
async def deploying_revision(
    db_with_cleanup: ExtendedAsyncSAEngine,
    listed_endpoint: tuple[uuid.UUID, str],
    test_image_id: uuid.UUID,
    test_scaling_group: str,
) -> uuid.UUID:
    """A second revision ``listed_endpoint`` is rolling out."""
    endpoint_id, _endpoint_name = listed_endpoint
    revision_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as sess:
        runtime_variant_id = await sess.scalar(
            sa.select(DeploymentRevisionRow.runtime_variant_id).where(
                DeploymentRevisionRow.endpoint == endpoint_id
            )
        )
        sess.add(
            DeploymentRevisionRow(
                id=revision_id,
                endpoint=endpoint_id,
                revision_number=2,
                image=test_image_id,
                model_mount_destination="/models",
                model_definition_path="deploying-definition.yaml",
                model_definition=ModelDefinition.model_validate({"models": []}),
                resource_group=test_scaling_group,
                resource_opts={},
                cluster_mode="single-node",
                cluster_size=1,
                environ={},
                runtime_variant_id=runtime_variant_id,
                extra_mounts=[],
            )
        )
        await sess.flush()
        await sess.execute(
            sa.update(EndpointRow)
            .where(EndpointRow.id == endpoint_id)
            .values(deploying_revision_id=revision_id)
        )
    return revision_id


@pytest.fixture
async def deploying_revision_without_current(
    db_with_cleanup: ExtendedAsyncSAEngine,
    listed_endpoint: tuple[uuid.UUID, str],
    deploying_revision: uuid.UUID,
) -> uuid.UUID:
    """``deploying_revision`` with the primary group serving no revision yet."""
    endpoint_id, _endpoint_name = listed_endpoint
    async with db_with_cleanup.begin_session() as sess:
        await sess.execute(
            sa.update(ReplicaGroupRow)
            .where(ReplicaGroupRow.deployment_id == endpoint_id)
            .values(current_revision_id=None)
        )
    return deploying_revision


@pytest.fixture
async def endpoint_without_revision(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_user: tuple[uuid.UUID, str],
    test_domain: DomainFixtureData,
    test_group_id: uuid.UUID,
    test_scaling_group: str,
) -> uuid.UUID:
    """An endpoint no revision has been made for."""
    user_id, _email = test_user
    endpoint_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            EndpointRow(
                id=endpoint_id,
                name=f"test-ep-{uuid.uuid4().hex[:8]}",
                created_user=user_id,
                session_owner=user_id,
                domain=test_domain.domain_name,
                project=test_group_id,
                resource_group=test_scaling_group,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=1,
            )
        )
    return endpoint_id


class TestGetEndpointByIdActiveRevision:
    async def test_the_current_revision_wins_over_the_deploying_one(
        self,
        repository: ModelServingRepository,
        listed_endpoint: tuple[uuid.UUID, str],
        deploying_revision: uuid.UUID,
    ) -> None:
        endpoint_id, _endpoint_name = listed_endpoint

        data = await repository.get_endpoint_by_id(endpoint_id)

        assert data is not None
        assert data.model_definition_path == "model-definition.yaml"

    async def test_the_deploying_revision_stands_in_without_a_current_one(
        self,
        repository: ModelServingRepository,
        listed_endpoint: tuple[uuid.UUID, str],
        deploying_revision_without_current: uuid.UUID,
    ) -> None:
        endpoint_id, _endpoint_name = listed_endpoint

        data = await repository.get_endpoint_by_id(endpoint_id)

        assert data is not None
        assert data.model_definition_path == "deploying-definition.yaml"

    async def test_an_endpoint_without_a_revision_answers_the_defaults(
        self,
        repository: ModelServingRepository,
        endpoint_without_revision: uuid.UUID,
    ) -> None:
        data = await repository.get_endpoint_by_id(endpoint_without_revision)

        assert data is not None
        assert data.image is None
        assert data.model == uuid.UUID(int=0)
        assert data.resource_slots == ResourceSlot({})
        assert data.runtime_variant_id is None
        assert data.routings == []
