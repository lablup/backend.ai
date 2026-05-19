from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.testutils.db import with_tables

_REQUIRED_TABLES = [
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
    ResourceSlotTypeRow,
    VFolderRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    DeploymentRevisionResourceSlotRow,
    EndpointRow,
]


class TestLegacyExtraMountsHydration:
    """BA-6102: legacy ``VFolderMount``-shaped extra_mounts must hydrate."""

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
    async def domain_name(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> str:
        name = f"d-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(DomainRow(name=name, total_resource_slots=ResourceSlot()))
        return name

    @pytest.fixture
    async def scaling_group_name(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> str:
        name = f"sg-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
        return name

    @pytest.fixture
    async def user_resource_policy_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str
    ) -> str:
        name = f"up-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
        return name

    @pytest.fixture
    async def project_resource_policy_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str
    ) -> str:
        name = f"pp-{suffix}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )
        return name

    @pytest.fixture
    async def user_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain_name: str,
        user_resource_policy_name: str,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
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
                    domain_name=domain_name,
                    resource_policy=user_resource_policy_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
            )
        return user_uuid

    @pytest.fixture
    async def project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain_name: str,
        project_resource_policy_name: str,
    ) -> uuid.UUID:
        project_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=project_uuid,
                    name=f"g-{suffix}",
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    resource_policy=project_resource_policy_name,
                )
            )
        return project_uuid

    @pytest.fixture
    async def image_id(self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str) -> ImageID:
        registry_uuid = uuid.uuid4()
        img_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ContainerRegistryRow(
                    id=registry_uuid,
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
            image.id = ImageID(img_uuid)
            db_sess.add(image)
        return ImageID(img_uuid)

    @pytest.fixture
    async def runtime_variant_id(
        self, db_with_cleanup: ExtendedAsyncSAEngine, suffix: str
    ) -> uuid.UUID:
        rv_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                RuntimeVariantRow(
                    id=rv_uuid,
                    name=f"rv-{suffix}",
                    description="test",
                )
            )
        return rv_uuid

    @pytest.fixture
    async def endpoint_with_revision(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        suffix: str,
        domain_name: str,
        scaling_group_name: str,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        image_id: ImageID,
        runtime_variant_id: uuid.UUID,
    ) -> tuple[DeploymentID, uuid.UUID]:
        """Create an endpoint + revision with empty ``extra_mounts``."""
        endpoint_id = DeploymentID(uuid.uuid4())
        revision_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"ep-{suffix}",
                    created_user=user_id,
                    session_owner=user_id,
                    domain=domain_name,
                    project=project_id,
                    resource_group=scaling_group_name,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.READY,
                    current_revision=revision_id,
                )
            )
            await db_sess.flush()
            db_sess.add(
                DeploymentRevisionRow(
                    id=revision_id,
                    endpoint=endpoint_id,
                    revision_number=1,
                    image=image_id,
                    model=None,
                    model_mount_destination="/models",
                    resource_group=scaling_group_name,
                    resource_opts={},
                    cluster_mode=ClusterMode.SINGLE_NODE.name,
                    cluster_size=1,
                    runtime_variant_id=runtime_variant_id,
                    environ={},
                    extra_mounts=[],
                )
            )
        return endpoint_id, revision_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=AsyncMock(),
            valkey_stat=AsyncMock(),
            valkey_live=AsyncMock(),
            valkey_schedule=AsyncMock(),
        )

    async def test_legacy_vfolder_mount_shape_hydrates_to_canonical_fields(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        deployment_repository: DeploymentRepository,
        endpoint_with_revision: tuple[DeploymentID, uuid.UUID],
    ) -> None:
        endpoint_id, revision_id = endpoint_with_revision
        legacy_vfolder_uuid = uuid.uuid4()
        legacy_quota_scope_uuid = uuid.uuid4()

        # Overwrite extra_mounts with a legacy ``VFolderMount.to_json()``
        # shaped payload — the exact shape rows persisted before commit
        # 8321c79aa (column-type switch) still carry today.
        legacy_payload = json.dumps([
            {
                "name": "weights-folder",
                "vfid": f"user:{legacy_quota_scope_uuid.hex}/{legacy_vfolder_uuid.hex}",
                "vfsubpath": "checkpoint",
                "host_path": "/vfroot/local/user:00/abc",
                "kernel_path": "/home/work/weights",
                "mount_perm": "rw",
                "usage_mode": "general",
            }
        ])
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.text(
                    "UPDATE deployment_revisions"
                    " SET extra_mounts = CAST(:payload AS jsonb)"
                    " WHERE id = :rev_id"
                ),
                {"payload": legacy_payload, "rev_id": revision_id},
            )

        result = await deployment_repository.get_deployments_by_ids({endpoint_id})

        assert len(result) == 1
        deployment = result[0]
        assert deployment.id == endpoint_id

        assert deployment.current_revision is not None
        mount_config = deployment.current_revision.model_mount_config
        assert len(mount_config.extra_mounts) == 1

        mount = mount_config.extra_mounts[0]
        assert mount.vfolder_id == legacy_vfolder_uuid
        assert mount.mount_destination == "/home/work/weights"
        assert mount.mount_perm == MountPermission.READ_WRITE
        assert mount.subpath == "checkpoint"
