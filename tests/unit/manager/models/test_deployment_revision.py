"""Tests for DeploymentRevisionRow model."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import BinarySize, ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
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
from ai.backend.manager.models.resource_slot.row import (
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestDeploymentRevisionRow:
    """Test cases for DeploymentRevisionRow model."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
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
                AgentRow,
                VFolderRow,
                ImageRow,
                ResourcePresetRow,
                ResourceSlotTypeRow,
                EndpointRow,
                DeploymentRevisionRow,
                DeploymentRevisionResourceSlotRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                SessionRow,
                KernelRow,
                RoutingRow,
            ],
        ):
            async with database_connection.begin_session() as sess:
                for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                    await sess.execute(
                        sa.text(
                            "INSERT INTO resource_slot_types (slot_name, slot_type, rank)"
                            " VALUES (:slot_name, :slot_type, 0)"
                            " ON CONFLICT DO NOTHING"
                        ),
                        {"slot_name": slot_name, "slot_type": slot_type},
                    )
            yield database_connection

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[DomainRow, None]:
        """Create test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain

    @pytest.fixture
    async def test_user_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[UserResourcePolicyRow, None]:
        """Create test user resource policy."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("10GiB")),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_user_resource_policy: UserResourcePolicyRow,
    ) -> AsyncGenerator[UserRow, None]:
        """Create test user."""
        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=create_test_password_info("test_password"),
                need_password_change=False,
                full_name="Test User",
                domain_name=test_domain.name,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                status_info="active",
                resource_policy=test_user_resource_policy.name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user

    @pytest.fixture
    async def test_project_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ProjectResourcePolicyRow, None]:
        """Create test project resource policy."""
        policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_project_resource_policy: ProjectResourcePolicyRow,
    ) -> AsyncGenerator[GroupRow, None]:
        """Create test group."""
        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=uuid.uuid4(),
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=test_domain.name,
                resource_policy=test_project_resource_policy.name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group

    @pytest.fixture
    async def test_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ImageRow, None]:
        """Create test image."""
        async with db_with_cleanup.begin_session() as db_sess:
            image = ImageRow(
                name="test-image:latest",
                project=str(uuid.uuid4()),
                image="test-image",
                registry="docker.io",
                registry_id=uuid.uuid4(),
                architecture="x86_64",
                is_local=False,
                config_digest="sha256:abc123",
                size_bytes=1000000,
                type=ImageType.COMPUTE,
                labels={},
            )
            db_sess.add(image)
            await db_sess.flush()

        yield image

    @pytest.fixture
    async def test_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ScalingGroupRow, None]:
        """Create test scaling group."""
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=sgroup_name,
                description="Test scaling group",
                is_active=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(sgroup)
            await db_sess.flush()

        yield sgroup

    @pytest.fixture
    async def test_endpoint(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_group: GroupRow,
        test_user: UserRow,
        test_image: ImageRow,
        test_scaling_group: ScalingGroupRow,
    ) -> AsyncGenerator[EndpointRow, None]:
        """Create test endpoint without an initial deployment revision."""
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint = EndpointRow(
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user.uuid,
                session_owner=test_user.uuid,
                replicas=1,
                domain=test_domain.name,
                project=test_group.id,
                resource_group=test_scaling_group.name,
                url=f"https://test-{uuid.uuid4().hex[:8]}.example.com",
                lifecycle_stage=EndpointLifecycle.CREATED,
            )
            db_sess.add(endpoint)
            await db_sess.flush()

        yield endpoint

    async def test_create_revision(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint: EndpointRow,
        test_image: ImageRow,
    ) -> None:
        """Test creating a deployment revision."""
        async with db_with_cleanup.begin_session() as db_sess:
            revision = DeploymentRevisionRow(
                endpoint=test_endpoint.id,
                revision_number=1,
                image=test_image.id,
                model=None,
                model_mount_destination="/models",
                resource_group="default",
                resource_opts={},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                runtime_variant=RuntimeVariant("custom"),
                environ={},
                extra_mounts=[],
            )
            revision.resource_slot_rows = [
                DeploymentRevisionResourceSlotRow(slot_name="cpu", quantity=Decimal("1")),
                DeploymentRevisionResourceSlotRow(slot_name="mem", quantity=Decimal("1024")),
            ]
            db_sess.add(revision)
            await db_sess.flush()

            assert revision.id is not None
            assert revision.endpoint == test_endpoint.id
            assert revision.revision_number == 1

    async def test_to_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint: EndpointRow,
        test_image: ImageRow,
    ) -> None:
        """Test converting revision to ModelRevisionData."""
        model_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            revision = DeploymentRevisionRow(
                endpoint=test_endpoint.id,
                revision_number=1,
                image=test_image.id,
                model=model_id,
                model_mount_destination="/models",
                model_definition_path="model.yaml",
                resource_group="default",
                resource_opts={"gpu_mem": "8G"},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                startup_command="python serve.py",
                bootstrap_script="#!/bin/bash\necho hello",
                runtime_variant=RuntimeVariant("custom"),
                environ={"DEBUG": "true"},
                extra_mounts=[],
            )
            revision.resource_slot_rows = [
                DeploymentRevisionResourceSlotRow(slot_name="cpu", quantity=Decimal("1")),
                DeploymentRevisionResourceSlotRow(slot_name="mem", quantity=Decimal("1024")),
            ]
            db_sess.add(revision)
            await db_sess.flush()

            # Refresh to ensure all attributes are loaded in the session context
            await db_sess.refresh(revision)

            data = revision.to_data()
            assert isinstance(data, ModelRevisionData)
            assert data.id == revision.id
            assert data.name == "revision-1"
            assert data.cluster_config.mode == ClusterMode.SINGLE_NODE
            assert data.cluster_config.size == 1
            assert data.resource_config.resource_group_name == "default"
            assert data.model_mount_config.vfolder_id == model_id
            assert data.model_mount_config.mount_destination == "/models"
            assert data.model_mount_config.definition_path == "model.yaml"
            assert data.model_runtime_config.runtime_variant == RuntimeVariant("custom")
            assert data.model_runtime_config.environ == {"DEBUG": "true"}
            assert data.image_id == test_image.id

    async def test_unique_constraint_endpoint_revision_number(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint: EndpointRow,
        test_image: ImageRow,
    ) -> None:
        """Test that endpoint + revision_number must be unique."""
        async with db_with_cleanup.begin_session() as db_sess:
            revision1 = DeploymentRevisionRow(
                endpoint=test_endpoint.id,
                revision_number=1,
                image=test_image.id,
                model=None,
                model_mount_destination="/models",
                resource_group="default",
                resource_opts={},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                runtime_variant=RuntimeVariant("custom"),
                environ={},
                extra_mounts=[],
            )
            revision1.resource_slot_rows = [
                DeploymentRevisionResourceSlotRow(slot_name="cpu", quantity=Decimal("1")),
                DeploymentRevisionResourceSlotRow(slot_name="mem", quantity=Decimal("1024")),
            ]
            db_sess.add(revision1)
            await db_sess.flush()

            # Try to create another revision with same endpoint + revision_number
            revision2 = DeploymentRevisionRow(
                endpoint=test_endpoint.id,
                revision_number=1,  # Same as revision1
                image=test_image.id,
                model=None,
                model_mount_destination="/models",
                resource_group="default",
                resource_opts={},
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                runtime_variant=RuntimeVariant("custom"),
                environ={},
                extra_mounts=[],
            )
            revision2.resource_slot_rows = [
                DeploymentRevisionResourceSlotRow(slot_name="cpu", quantity=Decimal("2")),
                DeploymentRevisionResourceSlotRow(slot_name="mem", quantity=Decimal("2048")),
            ]
            db_sess.add(revision2)

            with pytest.raises(sa.exc.IntegrityError):
                await db_sess.flush()

            # Rollback to clean up the session state after the expected error
            await db_sess.rollback()
