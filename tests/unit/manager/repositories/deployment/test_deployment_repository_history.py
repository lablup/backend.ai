"""Tests for DeploymentRepository history recording integration."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import AccessKey, BinarySize, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history import DeploymentHistoryRow, RouteHistoryRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import DeploymentConditions, DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import (
    EndpointLifecycleBatchUpdaterSpec,
    RouteBatchUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.scheduling_history.creators import (
    DeploymentHistoryCreatorSpec,
    RouteHistoryCreatorSpec,
)
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestUpdateEndpointLifecycleBulkWithHistory:
    """Tests for update_endpoint_lifecycle_bulk_with_history method."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                # FK order: parent -> child
                DomainRow,
                ScalingGroupRow,
                ResourcePresetRow,  # ScalingGroupRow relationship dependency
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,  # UserRow relationship dependency
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group and return name."""
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_container_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create test container registry and return registry ID."""
        registry_id = uuid.uuid4()
        registry_name = f"test-registry-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            registry = ContainerRegistryRow(
                id=registry_id,
                url="https://test-registry.example.com",
                registry_name=registry_name,
                type=ContainerRegistryType.DOCKER,
                project=None,
                is_global=True,
            )
            db_sess.add(registry)
            await db_sess.commit()

        return registry_id

    @pytest.fixture
    async def test_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_container_registry_id: uuid.UUID,
    ) -> uuid.UUID:
        """Create test image and return image ID."""
        image_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Get registry name
            registry_result = await db_sess.execute(
                sa.select(ContainerRegistryRow.registry_name).where(
                    ContainerRegistryRow.id == test_container_registry_id
                )
            )
            registry_name = registry_result.scalar_one()
            image_name = f"{registry_name}/test-image:latest"

            image = ImageRow(
                name=image_name,
                project=None,
                architecture="x86_64",
                registry_id=test_container_registry_id,
                is_local=False,
                registry=registry_name,
                image="test-image",
                tag="latest",
                config_digest="sha256:" + "a" * 64,
                size_bytes=100000000,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1073741824"}},
                status=ImageStatus.ALIVE,
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.commit()

        return image_id

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_pending_session_count=5,
                max_pending_session_resource_slots=ResourceSlot({
                    "cpu": Decimal("50"),
                    "mem": Decimal("51200"),
                }),
                max_containers_per_session=10,
                idle_timeout=3600,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test project resource policy and return policy name."""
        policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=create_test_password_info("testpass123"),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_keypair(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AccessKey:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIATEST{uuid.uuid4().hex[:12].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            # Get user email for user_id field
            user_result = await db_sess.execute(
                sa.select(UserRow.email).where(UserRow.uuid == test_user_uuid)
            )
            user_email = user_result.scalar_one()

            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="dummy-secret",
                user_id=user_email,
                user=test_user_uuid,
                is_active=True,
                resource_policy=test_keypair_resource_policy_name,
            )
            db_sess.add(keypair)
            await db_sess.commit()

        return access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain_name,
                resource_policy=test_project_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_pending_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair: AccessKey,
        test_image_id: uuid.UUID,
    ) -> uuid.UUID:
        """Create test endpoint in PENDING state and return endpoint ID."""
        endpoint_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user_uuid,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                resource_group=test_scaling_group_name,
                model=None,
                desired_replicas=1,
                image=test_image_id,  # Image required for non-DESTROYED lifecycle
                runtime_variant=RuntimeVariant.VLLM,
                url="http://test.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.PENDING,
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance with database and mocked dependencies."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.mark.asyncio
    async def test_updates_status_and_creates_history_atomically(
        self,
        deployment_repository: DeploymentRepository,
        test_pending_endpoint_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Status update and history are created in the same transaction."""
        # Test transition from PENDING to CREATED
        batch_updaters = [
            BatchUpdater(
                spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=EndpointLifecycle.CREATED),
                conditions=[
                    DeploymentConditions.by_ids([test_pending_endpoint_id]),
                    DeploymentConditions.by_lifecycle_stages([EndpointLifecycle.PENDING]),
                ],
            )
        ]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=test_pending_endpoint_id,
                phase="check_pending",
                result=SchedulingResult.SUCCESS,
                message="Test completed successfully",
                from_status=EndpointLifecycle.PENDING,
                to_status=EndpointLifecycle.CREATED,
            )
        ]

        updated_count = await deployment_repository.update_endpoint_lifecycle_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        assert updated_count == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Verify status update
            stmt = sa.select(EndpointRow).where(EndpointRow.id == test_pending_endpoint_id)
            endpoint = (await db_sess.execute(stmt)).scalar_one()
            assert endpoint.lifecycle_stage == EndpointLifecycle.CREATED

            # Verify history record
            stmt = sa.select(DeploymentHistoryRow).where(
                DeploymentHistoryRow.deployment_id == test_pending_endpoint_id
            )
            histories = (await db_sess.execute(stmt)).scalars().all()
            assert len(histories) == 1
            assert histories[0].phase == "check_pending"
            assert histories[0].result == str(SchedulingResult.SUCCESS)

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_batch_updaters(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Empty batch_updaters returns 0."""
        result = await deployment_repository.update_endpoint_lifecycle_bulk_with_history(
            [], BulkCreator(specs=[])
        )
        assert result == 0


class TestUpdateRouteStatusBulkWithHistory:
    """Tests for update_route_status_bulk_with_history method."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                # FK order: parent -> child
                DomainRow,
                ScalingGroupRow,
                ResourcePresetRow,  # ScalingGroupRow relationship dependency
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,  # UserRow relationship dependency
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain and return domain name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.commit()

        return domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test scaling group and return name."""
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
            await db_sess.commit()

        return sgroup_name

    @pytest.fixture
    async def test_container_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create test container registry and return registry ID."""
        registry_id = uuid.uuid4()
        registry_name = f"test-registry-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            registry = ContainerRegistryRow(
                id=registry_id,
                url="https://test-registry.example.com",
                registry_name=registry_name,
                type=ContainerRegistryType.DOCKER,
                project=None,
                is_global=True,
            )
            db_sess.add(registry)
            await db_sess.commit()

        return registry_id

    @pytest.fixture
    async def test_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_container_registry_id: uuid.UUID,
    ) -> uuid.UUID:
        """Create test image and return image ID."""
        image_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            # Get registry name
            registry_result = await db_sess.execute(
                sa.select(ContainerRegistryRow.registry_name).where(
                    ContainerRegistryRow.id == test_container_registry_id
                )
            )
            registry_name = registry_result.scalar_one()
            image_name = f"{registry_name}/test-image:latest"

            image = ImageRow(
                name=image_name,
                project=None,
                architecture="x86_64",
                registry_id=test_container_registry_id,
                is_local=False,
                registry=registry_name,
                image="test-image",
                tag="latest",
                config_digest="sha256:" + "a" * 64,
                size_bytes=100000000,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1073741824"}},
                status=ImageStatus.ALIVE,
            )
            image.id = image_id
            db_sess.add(image)
            await db_sess.commit()

        return image_id

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy and return policy name."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test keypair resource policy and return policy name."""
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots=ResourceSlot({
                    "cpu": Decimal("100"),
                    "mem": Decimal("102400"),
                }),
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_pending_session_count=5,
                max_pending_session_resource_slots=ResourceSlot({
                    "cpu": Decimal("50"),
                    "mem": Decimal("51200"),
                }),
                max_containers_per_session=10,
                idle_timeout=3600,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test project resource policy and return policy name."""
        policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                max_network_count=5,
            )
            db_sess.add(policy)
            await db_sess.commit()

        return policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user and return user UUID."""
        user_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=create_test_password_info("testpass123"),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.commit()

        return user_uuid

    @pytest.fixture
    async def test_keypair(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AccessKey:
        """Create test keypair and return access key."""
        access_key = AccessKey(f"AKIATEST{uuid.uuid4().hex[:12].upper()}")

        async with db_with_cleanup.begin_session() as db_sess:
            # Get user email for user_id field
            user_result = await db_sess.execute(
                sa.select(UserRow.email).where(UserRow.uuid == test_user_uuid)
            )
            user_email = user_result.scalar_one()

            keypair = KeyPairRow(
                access_key=access_key,
                secret_key="dummy-secret",
                user_id=user_email,
                user=test_user_uuid,
                is_active=True,
                resource_policy=test_keypair_resource_policy_name,
            )
            db_sess.add(keypair)
            await db_sess.commit()

        return access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test group and return group ID."""
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                domain_name=test_domain_name,
                resource_policy=test_project_resource_policy_name,
            )
            db_sess.add(group)
            await db_sess.commit()

        return group_id

    @pytest.fixture
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_keypair: AccessKey,
        test_image_id: uuid.UUID,
    ) -> uuid.UUID:
        """Create test endpoint and return endpoint ID."""
        endpoint_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            endpoint = EndpointRow(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user_uuid,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                resource_group=test_scaling_group_name,
                model=None,
                desired_replicas=1,
                image=test_image_id,  # Image required for non-DESTROYED lifecycle
                runtime_variant=RuntimeVariant.VLLM,
                url="http://test.example.com",
                open_to_public=False,
                lifecycle_stage=EndpointLifecycle.READY,
                resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            )
            db_sess.add(endpoint)
            await db_sess.commit()

        return endpoint_id

    @pytest.fixture
    async def test_provisioning_route_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_domain_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
    ) -> uuid.UUID:
        """Create test route in PROVISIONING state and return route ID."""
        route_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            route = RoutingRow(
                id=route_id,
                endpoint=test_endpoint_id,
                session=None,
                session_owner=test_user_uuid,
                domain=test_domain_name,
                project=test_group_id,
                status=RouteStatus.PROVISIONING,
                traffic_ratio=1.0,
            )
            db_sess.add(route)
            await db_sess.commit()

        return route_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance with database and mocked dependencies."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.mark.asyncio
    async def test_updates_status_and_creates_history_atomically(
        self,
        deployment_repository: DeploymentRepository,
        test_provisioning_route_id: uuid.UUID,
        test_endpoint_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Status update and history are created in the same transaction."""
        batch_updaters = [
            BatchUpdater(
                spec=RouteBatchUpdaterSpec(status=RouteStatus.HEALTHY),
                conditions=[
                    RouteConditions.by_ids([test_provisioning_route_id]),
                    RouteConditions.by_statuses([RouteStatus.PROVISIONING]),
                ],
            )
        ]
        history_specs = [
            RouteHistoryCreatorSpec(
                route_id=test_provisioning_route_id,
                deployment_id=test_endpoint_id,
                phase="provisioning",
                result=SchedulingResult.SUCCESS,
                message="Provisioning completed successfully",
                from_status=RouteStatus.PROVISIONING,
                to_status=RouteStatus.HEALTHY,
            )
        ]

        updated_count = await deployment_repository.update_route_status_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        assert updated_count == 1

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            # Verify status update
            stmt = sa.select(RoutingRow).where(RoutingRow.id == test_provisioning_route_id)
            route = (await db_sess.execute(stmt)).scalar_one()
            assert route.status == RouteStatus.HEALTHY

            # Verify history record
            stmt = sa.select(RouteHistoryRow).where(
                RouteHistoryRow.route_id == test_provisioning_route_id
            )
            histories = (await db_sess.execute(stmt)).scalars().all()
            assert len(histories) == 1
            assert histories[0].phase == "provisioning"
            assert histories[0].result == str(SchedulingResult.SUCCESS)

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_batch_updaters(
        self,
        deployment_repository: DeploymentRepository,
    ) -> None:
        """Empty batch_updaters returns 0."""
        result = await deployment_repository.update_route_status_bulk_with_history(
            [], BulkCreator(specs=[])
        )
        assert result == 0


class TestDeploymentHistoryMergeLogic:
    """Tests for deployment history merge logic."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                ResourcePresetRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_endpoint_with_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Create test endpoint with existing history record."""
        endpoint_id = uuid.uuid4()
        history_id = uuid.uuid4()
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        group_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        registry_id = uuid.uuid4()
        image_id = uuid.uuid4()
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        kp_policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
        proj_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )

            # Create scaling group
            db_sess.add(
                ScalingGroupRow(
                    name=sgroup_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )

            # Create resource policies
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("100"),
                        "mem": Decimal("102400"),
                    }),
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_pending_session_count=5,
                    max_pending_session_resource_slots=ResourceSlot({
                        "cpu": Decimal("50"),
                        "mem": Decimal("51200"),
                    }),
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=proj_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )

            # Create user
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                    password=create_test_password_info("testpass123"),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
            )

            # Create group
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=proj_policy_name,
                )
            )

            # Create registry and image
            registry_name = f"test-registry-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="https://test-registry.example.com",
                    registry_name=registry_name,
                    type=ContainerRegistryType.DOCKER,
                    project=None,
                    is_global=True,
                )
            )
            image = ImageRow(
                name=f"{registry_name}/test-image:latest",
                project=None,
                architecture="x86_64",
                registry_id=registry_id,
                is_local=False,
                registry=registry_name,
                image="test-image",
                tag="latest",
                config_digest="sha256:" + "a" * 64,
                size_bytes=100000000,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1073741824"}},
                status=ImageStatus.ALIVE,
            )
            image.id = image_id
            db_sess.add(image)

            # Create endpoint
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=group_id,
                    resource_group=sgroup_name,
                    model=None,
                    desired_replicas=1,
                    image=image_id,
                    runtime_variant=RuntimeVariant.VLLM,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.PENDING,
                    resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
                )
            )

            # Create existing history record
            db_sess.add(
                DeploymentHistoryRow(
                    id=history_id,
                    deployment_id=endpoint_id,
                    phase="validation",
                    from_status=str(EndpointLifecycle.PENDING.value),
                    to_status=str(EndpointLifecycle.PENDING.value),
                    result=str(SchedulingResult.FAILURE),
                    error_code="INSUFFICIENT_RESOURCE",
                    message="Not enough resources",
                    sub_steps=[],
                    attempts=1,
                )
            )

            await db_sess.commit()

        return endpoint_id, history_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.mark.asyncio
    async def test_merge_same_phase_error_to_status(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_with_history: tuple[uuid.UUID, uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Same phase, error_code, to_status should merge (increment attempts)."""
        endpoint_id, history_id = test_endpoint_with_history

        # Create new history with same phase, error_code, to_status
        batch_updaters = [
            BatchUpdater(
                spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=EndpointLifecycle.PENDING),
                conditions=[DeploymentConditions.by_ids([endpoint_id])],
            )
        ]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=endpoint_id,
                phase="validation",  # Same
                result=SchedulingResult.FAILURE,
                error_code="INSUFFICIENT_RESOURCE",  # Same
                message="Still not enough resources",
                from_status=EndpointLifecycle.PENDING,
                to_status=EndpointLifecycle.PENDING,  # Same
            )
        ]

        await deployment_repository.update_endpoint_lifecycle_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = sa.select(DeploymentHistoryRow).where(
                DeploymentHistoryRow.deployment_id == endpoint_id
            )
            histories = (await db_sess.execute(stmt)).scalars().all()

            # Should still be 1 record with incremented attempts
            assert len(histories) == 1
            assert histories[0].id == history_id
            assert histories[0].attempts == 2

    @pytest.mark.asyncio
    async def test_no_merge_different_phase(
        self,
        deployment_repository: DeploymentRepository,
        test_endpoint_with_history: tuple[uuid.UUID, uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Different phase should create new record."""
        endpoint_id, _ = test_endpoint_with_history

        batch_updaters = [
            BatchUpdater(
                spec=EndpointLifecycleBatchUpdaterSpec(lifecycle_stage=EndpointLifecycle.CREATED),
                conditions=[DeploymentConditions.by_ids([endpoint_id])],
            )
        ]
        history_specs = [
            DeploymentHistoryCreatorSpec(
                deployment_id=endpoint_id,
                phase="allocation",  # Different
                result=SchedulingResult.SUCCESS,
                error_code=None,
                message="Allocation succeeded",
                from_status=EndpointLifecycle.PENDING,
                to_status=EndpointLifecycle.CREATED,
            )
        ]

        await deployment_repository.update_endpoint_lifecycle_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = (
                sa.select(DeploymentHistoryRow)
                .where(DeploymentHistoryRow.deployment_id == endpoint_id)
                .order_by(DeploymentHistoryRow.created_at)
            )
            histories = (await db_sess.execute(stmt)).scalars().all()

            # Should be 2 records
            assert len(histories) == 2
            assert histories[0].phase == "validation"
            assert histories[0].attempts == 1
            assert histories[1].phase == "allocation"
            assert histories[1].attempts == 1


class TestRouteHistoryMergeLogic:
    """Tests for route history merge logic."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                ResourcePresetRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                SessionRow,
                EndpointRow,
                RoutingRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_route_with_history(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
        """Create test route with existing history record."""
        endpoint_id = uuid.uuid4()
        route_id = uuid.uuid4()
        history_id = uuid.uuid4()
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        group_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        registry_id = uuid.uuid4()
        image_id = uuid.uuid4()
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        kp_policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
        proj_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )

            # Create scaling group
            db_sess.add(
                ScalingGroupRow(
                    name=sgroup_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )

            # Create resource policies
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("100"),
                        "mem": Decimal("102400"),
                    }),
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_pending_session_count=5,
                    max_pending_session_resource_slots=ResourceSlot({
                        "cpu": Decimal("50"),
                        "mem": Decimal("51200"),
                    }),
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=proj_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )

            # Create user
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                    password=create_test_password_info("testpass123"),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
            )

            # Create group
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=proj_policy_name,
                )
            )

            # Create registry and image
            registry_name = f"test-registry-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="https://test-registry.example.com",
                    registry_name=registry_name,
                    type=ContainerRegistryType.DOCKER,
                    project=None,
                    is_global=True,
                )
            )
            image = ImageRow(
                name=f"{registry_name}/test-image:latest",
                project=None,
                architecture="x86_64",
                registry_id=registry_id,
                is_local=False,
                registry=registry_name,
                image="test-image",
                tag="latest",
                config_digest="sha256:" + "a" * 64,
                size_bytes=100000000,
                type=ImageType.COMPUTE,
                accelerators=None,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "1073741824"}},
                status=ImageStatus.ALIVE,
            )
            image.id = image_id
            db_sess.add(image)

            # Create endpoint
            db_sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=group_id,
                    resource_group=sgroup_name,
                    model=None,
                    desired_replicas=1,
                    image=image_id,
                    runtime_variant=RuntimeVariant.VLLM,
                    url="http://test.example.com",
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.READY,
                    resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
                )
            )

            # Create route
            db_sess.add(
                RoutingRow(
                    id=route_id,
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=group_id,
                    status=RouteStatus.PROVISIONING,
                    traffic_ratio=1.0,
                )
            )

            # Create existing history record
            db_sess.add(
                RouteHistoryRow(
                    id=history_id,
                    route_id=route_id,
                    deployment_id=endpoint_id,
                    phase="provisioning",
                    from_status=str(RouteStatus.PROVISIONING.value),
                    to_status=str(RouteStatus.PROVISIONING.value),
                    result=str(SchedulingResult.FAILURE),
                    error_code="SESSION_CREATION_FAILED",
                    message="Session creation failed",
                    sub_steps=[],
                    attempts=1,
                )
            )

            await db_sess.commit()

        return endpoint_id, route_id, history_id

    @pytest.fixture
    def deployment_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DeploymentRepository:
        """Create DeploymentRepository instance."""
        storage_manager = MagicMock()
        valkey_stat = MagicMock()
        valkey_live = MagicMock()
        valkey_schedule = MagicMock()

        return DeploymentRepository(
            db=db_with_cleanup,
            storage_manager=storage_manager,
            valkey_stat=valkey_stat,
            valkey_live=valkey_live,
            valkey_schedule=valkey_schedule,
        )

    @pytest.mark.asyncio
    async def test_merge_same_phase_error_to_status(
        self,
        deployment_repository: DeploymentRepository,
        test_route_with_history: tuple[uuid.UUID, uuid.UUID, uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Same phase, error_code, to_status should merge (increment attempts)."""
        endpoint_id, route_id, history_id = test_route_with_history

        batch_updaters = [
            BatchUpdater(
                spec=RouteBatchUpdaterSpec(status=RouteStatus.PROVISIONING),
                conditions=[RouteConditions.by_ids([route_id])],
            )
        ]
        history_specs = [
            RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=endpoint_id,
                phase="provisioning",  # Same
                result=SchedulingResult.FAILURE,
                error_code="SESSION_CREATION_FAILED",  # Same
                message="Session creation failed again",
                from_status=RouteStatus.PROVISIONING,
                to_status=RouteStatus.PROVISIONING,  # Same
            )
        ]

        await deployment_repository.update_route_status_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = sa.select(RouteHistoryRow).where(RouteHistoryRow.route_id == route_id)
            histories = (await db_sess.execute(stmt)).scalars().all()

            # Should still be 1 record with incremented attempts
            assert len(histories) == 1
            assert histories[0].id == history_id
            assert histories[0].attempts == 2

    @pytest.mark.asyncio
    async def test_no_merge_different_to_status(
        self,
        deployment_repository: DeploymentRepository,
        test_route_with_history: tuple[uuid.UUID, uuid.UUID, uuid.UUID],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Different to_status should create new record."""
        endpoint_id, route_id, _ = test_route_with_history

        batch_updaters = [
            BatchUpdater(
                spec=RouteBatchUpdaterSpec(status=RouteStatus.HEALTHY),
                conditions=[RouteConditions.by_ids([route_id])],
            )
        ]
        history_specs = [
            RouteHistoryCreatorSpec(
                route_id=route_id,
                deployment_id=endpoint_id,
                phase="provisioning",  # Same
                result=SchedulingResult.SUCCESS,
                error_code=None,
                message="Provisioning succeeded",
                from_status=RouteStatus.PROVISIONING,
                to_status=RouteStatus.HEALTHY,  # Different
            )
        ]

        await deployment_repository.update_route_status_bulk_with_history(
            batch_updaters,
            BulkCreator(specs=history_specs),
        )

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            stmt = (
                sa.select(RouteHistoryRow)
                .where(RouteHistoryRow.route_id == route_id)
                .order_by(RouteHistoryRow.created_at)
            )
            histories = (await db_sess.execute(stmt)).scalars().all()

            # Should be 2 records
            assert len(histories) == 2
            assert histories[0].to_status == str(RouteStatus.PROVISIONING.value)
            assert histories[0].attempts == 1
            assert histories[1].to_status == str(RouteStatus.HEALTHY.value)
            assert histories[1].attempts == 1
