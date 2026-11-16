"""
``ModelServingRepository.get_endpoint_access_validation_data`` reads the owner's
role by joining ``UserRow`` instead of loading ``EndpointRow.session_owner_row``.
The outer join must keep answering when no user row matches ``session_owner``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
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
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData


@pytest.fixture
async def db_with_cleanup(
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
async def test_domain(db_with_cleanup: ExtendedAsyncSAEngine) -> DomainFixtureData:
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
async def test_admin_user(
    db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
) -> uuid.UUID:
    """An ADMIN owner, so the assertion cannot pass on a default role."""
    user_id = uuid.uuid4()
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
                email=f"test-{uuid.uuid4().hex[:8]}@test.com",
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
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
        )
        await sess.flush()
    return user_id


@pytest.fixture
async def test_creator_user(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_domain: DomainFixtureData,
    test_admin_user: uuid.UUID,
) -> uuid.UUID:
    """A USER who created the endpoint, kept apart from its ADMIN owner."""
    user_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            UserRow(
                uuid=user_id,
                email=f"test-{uuid.uuid4().hex[:8]}@test.com",
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
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
        )
        await sess.flush()
    return user_id


@pytest.fixture
async def test_project_id(
    db_with_cleanup: ExtendedAsyncSAEngine, test_domain: DomainFixtureData
) -> uuid.UUID:
    project_id = uuid.uuid4()
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
                id=project_id,
                name=f"test-grp-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy="default",
            )
        )
        await sess.flush()
    return project_id


@pytest.fixture
def repository(db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
    return ModelServingRepository(
        db=db_with_cleanup,
        v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
        permission_check=MagicMock(),
    )


async def _add_endpoint(
    db: ExtendedAsyncSAEngine,
    *,
    created_user: uuid.UUID,
    session_owner: uuid.UUID,
    domain_name: str,
    project_id: uuid.UUID,
    resource_group: str,
) -> uuid.UUID:
    endpoint_id = uuid.uuid4()
    async with db.begin_session() as sess:
        sess.add(
            EndpointRow(
                id=endpoint_id,
                name=f"test-ep-{uuid.uuid4().hex[:8]}",
                created_user=created_user,
                session_owner=session_owner,
                domain=domain_name,
                project=project_id,
                resource_group=resource_group,
                lifecycle_stage=EndpointLifecycle.CREATED,
                replicas=1,
            )
        )
        await sess.flush()
    return endpoint_id


async def test_reads_owner_role_from_joined_user_row(
    db_with_cleanup: ExtendedAsyncSAEngine,
    repository: ModelServingRepository,
    test_admin_user: uuid.UUID,
    test_creator_user: uuid.UUID,
    test_domain: DomainFixtureData,
    test_project_id: uuid.UUID,
    test_scaling_group: str,
) -> None:
    endpoint_id = await _add_endpoint(
        db_with_cleanup,
        created_user=test_creator_user,
        session_owner=test_admin_user,
        domain_name=test_domain.domain_name,
        project_id=test_project_id,
        resource_group=test_scaling_group,
    )

    data = await repository.get_endpoint_access_validation_data(endpoint_id)

    assert data is not None
    assert data.session_owner_id == test_admin_user
    assert data.session_owner_role == UserRole.ADMIN
    assert data.domain == test_domain.domain_name


async def test_returns_none_for_unknown_endpoint(
    repository: ModelServingRepository,
) -> None:
    assert await repository.get_endpoint_access_validation_data(uuid.uuid4()) is None


async def test_role_is_none_when_owner_row_is_missing(
    db_with_cleanup: ExtendedAsyncSAEngine,
    repository: ModelServingRepository,
    test_domain: DomainFixtureData,
    test_project_id: uuid.UUID,
    test_scaling_group: str,
) -> None:
    """``session_owner`` carries no FK, so the outer join may find no user row."""
    orphan_owner = uuid.uuid4()
    endpoint_id = await _add_endpoint(
        db_with_cleanup,
        created_user=orphan_owner,
        session_owner=orphan_owner,
        domain_name=test_domain.domain_name,
        project_id=test_project_id,
        resource_group=test_scaling_group,
    )

    data = await repository.get_endpoint_access_validation_data(endpoint_id)

    assert data is not None
    assert data.session_owner_id == orphan_owner
    assert data.session_owner_role is None
    assert data.domain == test_domain.domain_name
