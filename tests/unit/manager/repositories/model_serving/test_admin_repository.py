"""
Tests for AdminModelServingRepository functionality.
Tests the admin repository layer with real database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.model_serving.types import (
    EndpointData,
    EndpointLifecycle,
    RoutingData,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestAdminModelServingRepository:
    """Test cases for AdminModelServingRepository."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                ResourcePresetRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                ImageRow,
                ImageAliasRow,
                SessionRow,
                KernelRow,
                RoutingRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AdminModelServingRepository:
        """Create repository with real database."""
        return AdminModelServingRepository(db=db_with_cleanup)

    @pytest.fixture
    async def test_domain(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DomainRow, None]:
        """Create test domain."""
        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=f"test-domain-{uuid.uuid4().hex[:8]}",
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()
        yield domain

    @pytest.fixture
    async def test_scaling_group(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ScalingGroupRow, None]:
        """Create test scaling group."""
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name=f"test-sgroup-{uuid.uuid4().hex[:8]}",
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
    async def test_user_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[UserResourcePolicyRow, None]:
        """Create test user resource policy."""
        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=f"test-urp-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=10,
                max_quota_scope_size=10 * 1024 * 1024 * 1024,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()
        yield policy

    @pytest.fixture
    async def test_project_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ProjectResourcePolicyRow, None]:
        """Create test project resource policy."""
        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=f"test-prp-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=10,
                max_quota_scope_size=100 * 1024 * 1024 * 1024,
                max_network_count=5,
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
                total_resource_slots={},
                allowed_vfolder_hosts={},
            )
            db_sess.add(group)
            await db_sess.flush()
        yield group

    @pytest.fixture
    async def test_image(
        self, db_with_cleanup: ExtendedAsyncSAEngine
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
    async def test_endpoint_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: DomainRow,
        test_group: GroupRow,
        test_user: UserRow,
        test_image: ImageRow,
        test_scaling_group: ScalingGroupRow,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test endpoint and return its ID."""
        async with db_with_cleanup.begin_session() as db_sess:
            endpoint = EndpointRow(
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=test_user.uuid,
                session_owner=test_user.uuid,
                replicas=3,
                image=test_image.id,
                domain=test_domain.name,
                project=test_group.id,
                resource_group=test_scaling_group.name,
                resource_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
                url=f"https://test-{uuid.uuid4().hex[:8]}.example.com",
                lifecycle_stage=EndpointLifecycle.CREATED,
                model_mount_destination="/models",
                cluster_mode=ClusterMode.SINGLE_NODE.name,
                cluster_size=1,
                runtime_variant=RuntimeVariant.CUSTOM,
                environ={},
                resource_opts={},
                extra_mounts=[],
            )
            db_sess.add(endpoint)
            await db_sess.flush()
            endpoint_id = endpoint.id
        yield endpoint_id

    @pytest.fixture
    async def test_route_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_endpoint_id: uuid.UUID,
        test_user: UserRow,
        test_domain: DomainRow,
        test_group: GroupRow,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test route and return its ID."""
        route_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            route = RoutingRow(
                id=route_id,
                endpoint=test_endpoint_id,
                session=None,
                session_owner=test_user.uuid,
                domain=test_domain.name,
                project=test_group.id,
                status=RouteStatus.HEALTHY,
                traffic_ratio=1.0,
            )
            db_sess.add(route)
            await db_sess.flush()
        yield route_id

    @pytest.fixture
    def mock_valkey_live(self) -> AsyncMock:
        """Create mock Valkey live client."""
        mock = AsyncMock()
        mock.store_live_data = AsyncMock()
        return mock

    # =========================================================================
    # Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_endpoint_by_id_force_success(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force retrieval of endpoint by ID without access checks."""
        result = await repository.get_endpoint_by_id_force(test_endpoint_id)

        assert result is not None
        assert isinstance(result, EndpointData)
        assert result.id == test_endpoint_id

    @pytest.mark.asyncio
    async def test_get_endpoint_by_id_force_not_found(
        self,
        repository: AdminModelServingRepository,
    ) -> None:
        """Test admin force retrieval returns None for non-existent endpoint."""
        result = await repository.get_endpoint_by_id_force(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_update_endpoint_lifecycle_force_success(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force update of endpoint lifecycle."""
        result = await repository.update_endpoint_lifecycle_force(
            test_endpoint_id, EndpointLifecycle.DESTROYING
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_endpoint_lifecycle_force_with_replicas(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force update of endpoint lifecycle with replicas."""
        result = await repository.update_endpoint_lifecycle_force(
            test_endpoint_id, EndpointLifecycle.CREATED, replicas=10
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_endpoint_lifecycle_force_not_found(
        self,
        repository: AdminModelServingRepository,
    ) -> None:
        """Test admin force update returns False for non-existent endpoint."""
        result = await repository.update_endpoint_lifecycle_force(
            uuid.uuid4(), EndpointLifecycle.DESTROYING
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_endpoint_errors_force_success(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force clear of endpoint errors."""
        result = await repository.clear_endpoint_errors_force(test_endpoint_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_clear_endpoint_errors_force_not_found(
        self,
        repository: AdminModelServingRepository,
    ) -> None:
        """Test admin force clear returns False for non-existent endpoint."""
        result = await repository.clear_endpoint_errors_force(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_get_route_by_id_force_success(
        self,
        repository: AdminModelServingRepository,
        test_route_id: uuid.UUID,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force retrieval of route by ID."""
        result = await repository.get_route_by_id_force(test_route_id, test_endpoint_id)

        assert result is not None
        assert isinstance(result, RoutingData)
        assert result.id == test_route_id

    @pytest.mark.asyncio
    async def test_get_route_by_id_force_wrong_service(
        self,
        repository: AdminModelServingRepository,
        test_route_id: uuid.UUID,
    ) -> None:
        """Test admin force retrieval returns None when route doesn't belong to service."""
        result = await repository.get_route_by_id_force(test_route_id, uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_decrease_endpoint_replicas_force_success(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force decrease of endpoint replicas."""
        result = await repository.decrease_endpoint_replicas_force(test_endpoint_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_endpoint_replicas_force_success(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
    ) -> None:
        """Test admin force update of endpoint replicas."""
        result = await repository.update_endpoint_replicas_force(test_endpoint_id, 8)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_endpoint_replicas_force_not_found(
        self,
        repository: AdminModelServingRepository,
    ) -> None:
        """Test admin force update replicas returns False for non-existent endpoint."""
        result = await repository.update_endpoint_replicas_force(uuid.uuid4(), 8)

        assert result is False

    @pytest.mark.asyncio
    async def test_update_route_traffic_force_success(
        self,
        repository: AdminModelServingRepository,
        test_route_id: uuid.UUID,
        test_endpoint_id: uuid.UUID,
        mock_valkey_live: AsyncMock,
    ) -> None:
        """Test admin force update of route traffic ratio."""
        new_traffic_ratio = 0.5

        result = await repository.update_route_traffic_force(
            mock_valkey_live, test_route_id, test_endpoint_id, new_traffic_ratio
        )

        assert result is not None
        assert isinstance(result, EndpointData)
        mock_valkey_live.store_live_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_route_traffic_force_route_not_found(
        self,
        repository: AdminModelServingRepository,
        test_endpoint_id: uuid.UUID,
        mock_valkey_live: AsyncMock,
    ) -> None:
        """Test admin force update traffic returns None for non-existent route."""
        result = await repository.update_route_traffic_force(
            mock_valkey_live, uuid.uuid4(), test_endpoint_id, 0.5
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_route_traffic_force_wrong_service(
        self,
        repository: AdminModelServingRepository,
        test_route_id: uuid.UUID,
        mock_valkey_live: AsyncMock,
    ) -> None:
        """Test admin force update traffic returns None when route doesn't belong to service."""
        result = await repository.update_route_traffic_force(
            mock_valkey_live, test_route_id, uuid.uuid4(), 0.5
        )

        assert result is None
