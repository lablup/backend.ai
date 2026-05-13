"""
Regression test for issue #11372 (expanded scope):
``ModelServingRepository.list_endpoints_by_owner_validated`` must drive
``EndpointRow.to_data()`` end-to-end without raising ``MissingGreenlet``.

The latent crash path is ``ModelServingService.list_serve``, which projects
each returned ``EndpointData`` and reads ``endpoint.routings`` plus the
revision-derived fields. Every relationship that ``to_data()`` traverses
must be eagerly loaded by the listing query — ``routings``,
``session_owner_row``, ``created_user_row``, and
``revisions`` -> ``image_row`` — or the sync projection lazy-loads inside
an async transaction and SQLAlchemy raises
``sqlalchemy.exc.MissingGreenlet``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.config import ModelDefinition
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_serving.types import EndpointData, EndpointLifecycle
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Provision the table set ``list_endpoints_by_owner_validated`` exercises."""
    async with with_tables(
        database_connection,
        [
            DomainRow,
            ScalingGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            UserRow,
            KeyPairRow,
            GroupRow,
            ContainerRegistryRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
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
async def test_domain(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
    name = f"test-domain-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(DomainRow(name=name, total_resource_slots=ResourceSlot()))
        await sess.flush()
    return name


@pytest.fixture
async def test_scaling_group(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
    name = f"test-sg-{uuid.uuid4().hex[:8]}"
    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            ScalingGroupRow(
                name=name,
                driver="static",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
        )
        await sess.flush()
    return name


@pytest.fixture
async def test_user(
    db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str
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
                domain_name=test_domain,
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
                user_id=email,
                access_key="TESTKEY",
                secret_key="TESTSECRET",
                is_active=True,
                is_admin=True,
                user=user_id,
                resource_policy="default",
            )
        )
        await sess.flush()
        await sess.execute(
            sa.update(UserRow).where(UserRow.uuid == user_id).values(main_access_key="TESTKEY")
        )
        await sess.flush()
    return user_id, email


@pytest.fixture
async def test_group_id(db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str) -> uuid.UUID:
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
            GroupRow(
                id=group_id,
                name=f"test-grp-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain,
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
                id=registry_id,
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
    test_domain: str,
    test_group_id: uuid.UUID,
    test_scaling_group: str,
    test_image_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    """Create a CREATED endpoint with one revision (current) and one route
    so ``list_endpoints_by_owner_validated`` returns it. Returns
    ``(endpoint_id, owner_email)``.
    """
    user_id, _email = test_user
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
                created_user=user_id,
                session_owner=user_id,
                domain=test_domain,
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
                default_model_definition=ModelDefinition.model_validate({"models": []}),
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

        await sess.execute(
            sa.update(EndpointRow)
            .where(EndpointRow.id == endpoint_id)
            .values(current_revision=revision_id)
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
                domain=test_domain,
                project=test_group_id,
                revision=revision_id,
            )
        )
        await sess.flush()

    return endpoint_id, endpoint_name


@pytest.fixture
def repository(db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
    return ModelServingRepository(db=db_with_cleanup)


async def test_list_endpoints_by_owner_validated_drives_to_data_end_to_end(
    repository: ModelServingRepository,
    test_user: tuple[uuid.UUID, str],
    listed_endpoint: tuple[uuid.UUID, str],
) -> None:
    """``list_endpoints_by_owner_validated`` must return ``EndpointData``
    with every relationship-derived field populated — owner email
    (``session_owner_row``), routings, and revision-derived fields
    (``revisions`` -> ``image_row``).

    Without eager-loading all four relationships, ``to_data()`` lazy-loads
    them inside the async transaction and SQLAlchemy raises
    ``sqlalchemy.exc.MissingGreenlet`` (the latent crash path that
    ``ModelServingService.list_serve`` exposes through
    ``GET /services``).
    """
    user_id, owner_email = test_user
    endpoint_id, endpoint_name = listed_endpoint

    results = await repository.list_endpoints_by_owner_validated(user_id)

    assert len(results) == 1
    endpoint = results[0]
    assert isinstance(endpoint, EndpointData)
    assert endpoint.id == endpoint_id
    assert endpoint.name == endpoint_name
    # session_owner_row -> session_owner_email; defaults to "" if missing.
    assert endpoint.session_owner_email == owner_email
    # created_user_row -> created_user_email; defaults to None if missing.
    assert endpoint.created_user_email == owner_email
    # revisions -> image_row -> EndpointData.image; falls back to None
    # when revisions are not loaded.
    assert endpoint.image is not None
    # routings is sourced from EndpointRow.routings; defaults to [] if
    # the relationship is not loaded.
    assert len(endpoint.routings) == 1
