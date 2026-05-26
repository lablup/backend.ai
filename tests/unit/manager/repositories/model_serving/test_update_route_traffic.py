"""
Regression test for issue #11372: ``ModelServingRepository.update_route_traffic``
returning ``EndpointData`` for an endpoint that owns a persisted
``DeploymentRevisionRow`` must not raise ``MissingGreenlet``.

Without the fix, ``EndpointRow.to_data`` lazy-loads ``revisions`` outside of
SQLAlchemy's greenlet bridge and raises ``sqlalchemy.exc.MissingGreenlet``.
With the fix the call site eagerly loads ``revisions`` (and
``revisions.image_row``) so the projection runs entirely on cached state.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
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
    """Provision the table set ``update_route_traffic`` exercises."""
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
async def test_user_id(db_with_cleanup: ExtendedAsyncSAEngine, test_domain: str) -> uuid.UUID:
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
    return user_id


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
async def endpoint_with_revision_and_route(
    db_with_cleanup: ExtendedAsyncSAEngine,
    test_user_id: uuid.UUID,
    test_domain: str,
    test_group_id: uuid.UUID,
    test_scaling_group: str,
    test_image_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create an endpoint with one revision (current) and one route. Returns
    ``(endpoint_id, route_id)`` so the caller can drive ``update_route_traffic``."""
    endpoint_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    route_id = uuid.uuid4()
    runtime_variant_id = uuid.uuid4()

    async with db_with_cleanup.begin_session() as sess:
        sess.add(
            EndpointRow(
                id=endpoint_id,
                name=f"test-ep-{uuid.uuid4().hex[:8]}",
                created_user=test_user_id,
                session_owner=test_user_id,
                domain=test_domain,
                project=test_group_id,
                resource_group=test_scaling_group,
                lifecycle_stage=EndpointLifecycle.READY,
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
                session_owner=test_user_id,
                domain=test_domain,
                project=test_group_id,
                revision=revision_id,
            )
        )
        await sess.flush()

    return endpoint_id, route_id


@pytest.fixture
def repository(db_with_cleanup: ExtendedAsyncSAEngine) -> ModelServingRepository:
    return ModelServingRepository(db=db_with_cleanup)


@pytest.fixture
def mock_valkey_live() -> MagicMock:
    """Stub Valkey client — ``update_route_traffic`` only writes a key."""
    mock = MagicMock(spec=ValkeyLiveClient)
    mock.store_live_data = AsyncMock()
    return mock


async def test_update_route_traffic_returns_endpoint_data_when_revision_exists(
    repository: ModelServingRepository,
    endpoint_with_revision_and_route: tuple[uuid.UUID, uuid.UUID],
    mock_valkey_live: MagicMock,
) -> None:
    """``update_route_traffic`` must return ``EndpointData`` (not raise
    ``MissingGreenlet``) for an endpoint that already has a persisted
    revision row.

    Regression for lablup/backend.ai#11372: without the ``load_revisions=True``
    eager-load on the post-update endpoint fetch, ``EndpointRow.to_data``
    lazily walks ``self.revisions`` and SQLAlchemy raises
    ``MissingGreenlet`` because ``to_data`` is sync code invoked from an
    async coroutine without a greenlet bridge.
    """
    endpoint_id, route_id = endpoint_with_revision_and_route

    result = await repository.update_route_traffic(
        valkey_live=mock_valkey_live,
        route_id=route_id,
        service_id=endpoint_id,
        traffic_ratio=0.0,
    )

    assert result is not None
    assert isinstance(result, EndpointData)
    assert result.id == endpoint_id
    # The eager-loaded revision must have flowed through to_data() —
    # if revisions were missing the projection falls back to defaults.
    assert result.image is not None
    mock_valkey_live.store_live_data.assert_awaited_once()
