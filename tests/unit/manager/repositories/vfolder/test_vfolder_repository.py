"""
Tests for VfolderRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.storage import (
    VFolderFilterStatusFailed,
    VFolderHasLinkedModelCard,
    VFolderNotFound,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.vfolder.purgers import VFolderPurgerSpec
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.updaters import VFolderTrashUpdaterSpec
from ai.backend.testutils.db import with_tables


class TestVfolderRepository:
    """Test cases for VfolderRepository"""

    def _make_vfolder_create_params(
        self,
        *,
        folder_id: uuid.UUID,
        domain_name: str,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        permission: VFolderMountPermission = VFolderMountPermission.READ_ONLY,
        usage_mode: VFolderUsageMode = VFolderUsageMode.MODEL,
    ) -> VFolderCreateParams:
        """Create VFolderCreateParams for testing."""
        return VFolderCreateParams(
            id=folder_id,
            name=f"test-model-{folder_id.hex[:8]}",
            domain_name=domain_name,
            quota_scope_id=f"project:{group_id}",
            usage_mode=usage_mode,
            permission=permission,
            host="local",
            creator=f"test-{user_id.hex[:8]}@example.com",
            creator_id=user_id,
            ownership_type=VFolderOwnershipType.GROUP,
            user=user_id,
            group=group_id,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
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
                RoutingRow,
                ResourcePresetRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
                ObjectPermissionRow,
                PermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for vfolder",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test project resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

            # Create system role for the user
            role_id = uuid.uuid4()
            role = RoleRow(
                id=role_id,
                name=f"user-role-{user_uuid.hex[:8]}",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Map user to the system role
            user_role = UserRoleRow(
                user_id=user_uuid,
                role_id=role_id,
            )
            db_sess.add(user_role)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_model_store_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test model-store group and return group UUID"""
        group_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test-model-store-{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                description="Test model-store group",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.MODEL_STORE,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_uuid

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[VfolderRepository, None]:
        """Create VfolderRepository instance with database"""
        repo = VfolderRepository(db=db_with_cleanup)
        yield repo

    async def test_model_store_vfolder_permission_is_overridden_to_read_only(
        self,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_user: uuid.UUID,
        test_model_store_group: uuid.UUID,
    ) -> None:
        """Test that model-store vfolder permission is always READ_ONLY.

        The service layer (VFolderService.create) overrides any requested permission
        to READ_ONLY for model-store group type. This test verifies that the repository
        correctly stores the READ_ONLY permission received from the service layer.
        """
        folder_id = uuid.uuid4()
        params = self._make_vfolder_create_params(
            folder_id=folder_id,
            domain_name=test_domain_name,
            group_id=test_model_store_group,
            user_id=test_user,
            permission=VFolderMountPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.MODEL,
        )

        vfolder_data = await vfolder_repository.create_vfolder_with_permission(
            params, create_owner_permission=True
        )

        assert vfolder_data.id == folder_id
        assert vfolder_data.name == params.name
        assert vfolder_data.permission == VFolderMountPermission.READ_ONLY
        assert vfolder_data.usage_mode == VFolderUsageMode.MODEL
        assert vfolder_data.ownership_type == VFolderOwnershipType.GROUP
        assert vfolder_data.group == test_model_store_group


class TestVfolderRepositoryAllowedVfolderHosts:
    """Tests for VfolderRepository.get_allowed_vfolder_hosts() method"""

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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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

        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test project resource policy."""
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user."""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        return user_uuid

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create a group with allowed_vfolder_hosts set."""
        group_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test-group-{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                description="Test group with vfolder hosts",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={
                    "local": ["create-vfolder", "mount-in-session"],
                },
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()

        return group_uuid

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        """Create VfolderRepository instance."""
        return VfolderRepository(db=db_with_cleanup)

    async def test_get_allowed_vfolder_hosts_returns_vfolder_host_permission_map(
        self,
        vfolder_repository: VfolderRepository,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> None:
        """Test that get_allowed_vfolder_hosts returns VFolderHostPermissionMap type."""
        result = await vfolder_repository.get_allowed_vfolder_hosts(
            user_uuid=test_user,
            group_uuid=test_group,
        )

        assert isinstance(result, VFolderHostPermissionMap)

    # -- get_user_with_keypair_policy_vfolder_hosts --

    @pytest.fixture
    async def keypair_policy_with_hosts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """KeyPair resource policy with non-empty allowed_vfolder_hosts."""
        policy_name = f"test-kp-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=0,
                allowed_vfolder_hosts=VFolderHostPermissionMap({
                    "local:volume1": {
                        VFolderHostPermission.CREATE,
                        VFolderHostPermission.MODIFY,
                    },
                }),
            )
            db_sess.add(policy)
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def user_with_active_keypair(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user: uuid.UUID,
        keypair_policy_with_hosts: str,
    ) -> uuid.UUID:
        """Bind an active keypair (pointing to keypair_policy_with_hosts) to ``test_user``."""
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
                    user_id=f"test-{test_user.hex[:8]}@example.com",
                    user=test_user,
                    access_key=f"AK{test_user.hex[:14]}",
                    secret_key="test-secret",
                    is_active=True,
                    is_admin=False,
                    resource_policy=keypair_policy_with_hosts,
                    rate_limit=1000,
                )
            )
            await db_sess.flush()
        return test_user

    async def test_get_user_with_keypair_policy_vfolder_hosts_success(
        self,
        vfolder_repository: VfolderRepository,
        user_with_active_keypair: uuid.UUID,
    ) -> None:
        """Returns email/role and the merged allowed_vfolder_hosts from active keypairs."""
        result = await vfolder_repository.get_user_with_keypair_policy_vfolder_hosts(
            user_with_active_keypair
        )
        assert result.email == f"test-{user_with_active_keypair.hex[:8]}@example.com"
        assert result.role == UserRole.USER
        assert "local:volume1" in result.allowed_vfolder_hosts
        assert result.allowed_vfolder_hosts["local:volume1"] == {
            VFolderHostPermission.CREATE,
            VFolderHostPermission.MODIFY,
        }

    async def test_get_user_with_keypair_policy_vfolder_hosts_user_not_found(
        self,
        vfolder_repository: VfolderRepository,
    ) -> None:
        """Unknown user UUID raises UserNotFound."""
        with pytest.raises(UserNotFound):
            await vfolder_repository.get_user_with_keypair_policy_vfolder_hosts(uuid.uuid4())


class TestVfolderRepositoryPurge:
    """Tests for VfolderRepository.purge_vfolder() method"""

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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                ModelCardRow,
                EntityFieldRow,
                AssociationScopesEntitiesRow,
                ObjectPermissionRow,
                PermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
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

        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user."""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        return user_uuid

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        """Create VfolderRepository instance."""
        return VfolderRepository(db=db_with_cleanup)

    async def _create_vfolder_in_db(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        vfolder_id: uuid.UUID,
        domain_name: str,
        user_id: uuid.UUID,
        status: VFolderOperationStatus,
    ) -> None:
        """Helper to create a vfolder directly in DB."""
        async with db.begin_session() as db_sess:
            vfolder = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                host="local:volume1",
                domain_name=domain_name,
                quota_scope_id=f"user:{user_id}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                max_files=0,
                max_size=None,
                num_files=0,
                cur_size=0,
                creator=f"test-{user_id.hex[:8]}@example.com",
                unmanaged_path=None,
                ownership_type=VFolderOwnershipType.USER,
                user=user_id,
                group=None,
                cloneable=False,
                status=status,
            )
            db_sess.add(vfolder)
            await db_sess.flush()

    async def _vfolder_exists(self, db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> bool:
        """Check if vfolder exists in DB."""
        async with db.begin_readonly_session() as session:
            query = sa.select(VFolderRow.id).where(VFolderRow.id == vfolder_id)
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @pytest.fixture
    async def vfolder_in_db(
        self,
        request: pytest.FixtureRequest,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user: uuid.UUID,
    ) -> uuid.UUID:
        """Create a vfolder with the given status in DB."""
        status: VFolderOperationStatus = request.param
        vfolder_id = uuid.uuid4()
        await self._create_vfolder_in_db(
            db_with_cleanup,
            vfolder_id=vfolder_id,
            domain_name=test_domain_name,
            user_id=test_user,
            status=status,
        )
        return vfolder_id

    @pytest.mark.parametrize(
        "vfolder_in_db",
        [
            VFolderOperationStatus.DELETE_COMPLETE,
            VFolderOperationStatus.DELETE_PENDING,
        ],
        ids=["delete_complete", "delete_pending"],
        indirect=True,
    )
    async def test_purge_vfolder_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        vfolder_in_db: uuid.UUID,
    ) -> None:
        """Test successful purge of vfolder with purgable status."""
        vfolder_id = vfolder_in_db

        # Verify vfolder exists before purge
        assert await self._vfolder_exists(db_with_cleanup, vfolder_id)

        purger = RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=vfolder_id,
            spec=VFolderPurgerSpec(vfolder_id=vfolder_id),
        )
        result = await vfolder_repository.purge_vfolder(purger)

        assert result.id == vfolder_id

        # Verify vfolder is deleted from DB
        assert not await self._vfolder_exists(db_with_cleanup, vfolder_id)

    async def test_purge_vfolder_not_found(
        self,
        vfolder_repository: VfolderRepository,
    ) -> None:
        """Test purge fails when vfolder doesn't exist."""
        non_existent_id = uuid.uuid4()
        purger = RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=non_existent_id,
            spec=VFolderPurgerSpec(vfolder_id=non_existent_id),
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_repository.purge_vfolder(purger)

    @pytest.mark.parametrize(
        "vfolder_in_db",
        [
            VFolderOperationStatus.READY,
            VFolderOperationStatus.PERFORMING,
            VFolderOperationStatus.CLONING,
            VFolderOperationStatus.MOUNTED,
            VFolderOperationStatus.DELETE_ONGOING,
            VFolderOperationStatus.DELETE_ERROR,
        ],
        ids=["ready", "performing", "cloning", "mounted", "delete_ongoing", "delete_error"],
        indirect=True,
    )
    async def test_purge_vfolder_invalid_status(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        vfolder_in_db: uuid.UUID,
    ) -> None:
        """Test purge fails when vfolder has non-purgable status."""
        vfolder_id = vfolder_in_db

        purger = RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=vfolder_id,
            spec=VFolderPurgerSpec(vfolder_id=vfolder_id),
        )

        with pytest.raises(VFolderFilterStatusFailed):
            await vfolder_repository.purge_vfolder(purger)

        # Verify vfolder still exists in DB (not deleted)
        assert await self._vfolder_exists(db_with_cleanup, vfolder_id)

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    domain_name=test_domain_name,
                    is_active=True,
                    type=ProjectType.GENERAL,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_project_resource_policy_name,
                )
            )
            await db_sess.flush()
        return project_id

    @pytest.fixture
    async def linked_model_card_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_in_db: uuid.UUID,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> uuid.UUID:
        """Create a ModelCardRow that references ``vfolder_in_db``.

        The FK on ``model_cards.vfolder`` is ``ondelete='RESTRICT'``, so the
        presence of this row is what triggers the integrity violation under
        test.
        """
        card_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ModelCardRow(
                    id=card_id,
                    name=f"mc-{card_id.hex[:8]}",
                    vfolder=vfolder_in_db,
                    domain=test_domain_name,
                    project=test_project_id,
                    creator=test_user,
                )
            )
            await db_sess.flush()
        return card_id

    @pytest.mark.parametrize(
        "vfolder_in_db",
        [VFolderOperationStatus.DELETE_PENDING],
        ids=["delete_pending"],
        indirect=True,
    )
    async def test_purge_vfolder_with_linked_model_card_raises(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        vfolder_in_db: uuid.UUID,
        linked_model_card_id: uuid.UUID,
    ) -> None:
        """The ``ondelete='RESTRICT'`` FK on ``model_cards.vfolder`` blocks the
        underlying DELETE; the repository must surface that as a domain-level
        ``VFolderHasLinkedModelCard`` (translated from the parsed integrity
        error by SQLSTATE + constraint name) without leaking the raw
        ``IntegrityError`` to callers, and without modifying either row.
        """
        vfolder_id = vfolder_in_db

        purger = RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=vfolder_id,
            spec=VFolderPurgerSpec(vfolder_id=vfolder_id),
        )

        with pytest.raises(VFolderHasLinkedModelCard):
            await vfolder_repository.purge_vfolder(purger)

        assert await self._vfolder_exists(db_with_cleanup, vfolder_id)
        async with db_with_cleanup.begin_readonly_session() as session:
            assert (
                await session.execute(
                    sa.select(ModelCardRow.id).where(ModelCardRow.id == linked_model_card_id)
                )
            ).scalar_one_or_none() is not None


class TestVfolderRepositoryDeleteForever:
    """Tests for VfolderRepository.delete_vfolders_forever() with cascade_model_card."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                VFolderInvitationRow,
                VFolderPermissionRow,
                ResourceSlotTypeRow,
                ModelCardRow,
                ModelCardResourceRequirementRow,
                EntityFieldRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()
        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"testuser-{user_uuid.hex[:8]}",
                    email=f"test-{user_uuid.hex[:8]}@example.com",
                    password=password_info,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=test_domain_name,
                    role=UserRole.USER,
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        return user_uuid

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            await db_sess.flush()
        return policy_name

    @pytest.fixture
    async def test_project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name=f"test-project-{project_id.hex[:8]}",
                    domain_name=test_domain_name,
                    is_active=True,
                    type=ProjectType.GENERAL,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_project_resource_policy_name,
                )
            )
            await db_sess.flush()
        return project_id

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    async def _create_vfolder(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        user_id: uuid.UUID,
        status: VFolderOperationStatus = VFolderOperationStatus.DELETE_PENDING,
    ) -> uuid.UUID:
        vfolder_id = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"test-vfolder-{vfolder_id.hex[:8]}",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator=f"test-{user_id.hex[:8]}@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_id,
                    group=None,
                    cloneable=False,
                    status=status,
                )
            )
            await db_sess.flush()
        return vfolder_id

    async def _create_model_card(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        vfolder_id: uuid.UUID,
        domain_name: str,
        project_id: uuid.UUID,
        creator_id: uuid.UUID,
    ) -> uuid.UUID:
        card_id = uuid.uuid4()
        async with db.begin_session() as db_sess:
            db_sess.add(
                ModelCardRow(
                    id=card_id,
                    name=f"mc-{card_id.hex[:8]}",
                    vfolder=vfolder_id,
                    domain=domain_name,
                    project=project_id,
                    creator=creator_id,
                )
            )
            await db_sess.flush()
        return card_id

    async def _vfolder_status(
        self,
        db: ExtendedAsyncSAEngine,
        vfolder_id: uuid.UUID,
    ) -> VFolderOperationStatus | None:
        async with db.begin_readonly_session() as session:
            return (
                await session.execute(
                    sa.select(VFolderRow.status).where(VFolderRow.id == vfolder_id)
                )
            ).scalar_one_or_none()

    async def _model_card_exists(
        self,
        db: ExtendedAsyncSAEngine,
        card_id: uuid.UUID,
    ) -> bool:
        async with db.begin_readonly_session() as session:
            row = (
                await session.execute(sa.select(ModelCardRow.id).where(ModelCardRow.id == card_id))
            ).scalar_one_or_none()
            return row is not None

    async def test_no_linked_card_succeeds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_user: uuid.UUID,
    ) -> None:
        vfolder_id = await self._create_vfolder(
            db_with_cleanup, domain_name=test_domain_name, user_id=test_user
        )

        result = await vfolder_repository.delete_vfolders_forever([vfolder_id])

        assert len(result.succeeded) == 1
        assert result.succeeded[0].id == vfolder_id
        assert result.failures == []
        assert (
            await self._vfolder_status(db_with_cleanup, vfolder_id)
            == VFolderOperationStatus.DELETE_ONGOING
        )

    async def test_linked_card_without_cascade_returns_failure(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        vfolder_id = await self._create_vfolder(
            db_with_cleanup, domain_name=test_domain_name, user_id=test_user
        )
        card_id = await self._create_model_card(
            db_with_cleanup,
            vfolder_id=vfolder_id,
            domain_name=test_domain_name,
            project_id=test_project_id,
            creator_id=test_user,
        )

        result = await vfolder_repository.delete_vfolders_forever([vfolder_id])

        assert result.succeeded == []
        assert len(result.failures) == 1
        assert result.failures[0].vfolder_id == vfolder_id
        assert isinstance(result.failures[0].exception, VFolderHasLinkedModelCard)
        # vfolder + card both untouched
        assert (
            await self._vfolder_status(db_with_cleanup, vfolder_id)
            == VFolderOperationStatus.DELETE_PENDING
        )
        assert await self._model_card_exists(db_with_cleanup, card_id)

    async def test_linked_card_with_cascade_succeeds_and_removes_card(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        vfolder_id = await self._create_vfolder(
            db_with_cleanup, domain_name=test_domain_name, user_id=test_user
        )
        card_id = await self._create_model_card(
            db_with_cleanup,
            vfolder_id=vfolder_id,
            domain_name=test_domain_name,
            project_id=test_project_id,
            creator_id=test_user,
        )

        result = await vfolder_repository.delete_vfolders_forever(
            [vfolder_id], cascade_model_card=True
        )

        assert len(result.succeeded) == 1
        assert result.succeeded[0].id == vfolder_id
        assert result.failures == []
        assert (
            await self._vfolder_status(db_with_cleanup, vfolder_id)
            == VFolderOperationStatus.DELETE_ONGOING
        )
        assert not await self._model_card_exists(db_with_cleanup, card_id)

    async def test_mixed_batch_partitions_results(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_project_id: uuid.UUID,
        test_user: uuid.UUID,
    ) -> None:
        plain_id = await self._create_vfolder(
            db_with_cleanup, domain_name=test_domain_name, user_id=test_user
        )
        carded_id = await self._create_vfolder(
            db_with_cleanup, domain_name=test_domain_name, user_id=test_user
        )
        card_id = await self._create_model_card(
            db_with_cleanup,
            vfolder_id=carded_id,
            domain_name=test_domain_name,
            project_id=test_project_id,
            creator_id=test_user,
        )

        result = await vfolder_repository.delete_vfolders_forever([plain_id, carded_id])

        assert [d.id for d in result.succeeded] == [plain_id]
        assert len(result.failures) == 1
        assert result.failures[0].vfolder_id == carded_id
        assert (
            await self._vfolder_status(db_with_cleanup, plain_id)
            == VFolderOperationStatus.DELETE_ONGOING
        )
        assert (
            await self._vfolder_status(db_with_cleanup, carded_id)
            == VFolderOperationStatus.DELETE_PENDING
        )
        assert await self._model_card_exists(db_with_cleanup, card_id)


class TestVFolderRepositoryTrashAndRestore:
    """Tests for trash_vfolder() and restore_vfolders_from_trash()."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
                VFolderRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                AgentRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    @pytest.fixture
    async def ready_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create a READY vfolder in DB and return its ID."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        vfolder_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="test",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
            password_info = PasswordInfo(
                password="dummy",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=600_000,
                salt_size=32,
            )
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u-{user_uuid.hex[:8]}",
                    email=f"u-{user_uuid.hex[:8]}@test.local",
                    password=password_info,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name=f"test-vf-{vfolder_id.hex[:8]}",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_uuid}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator=f"u-{user_uuid.hex[:8]}@test.local",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_uuid,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await db_sess.flush()

        return vfolder_id

    # -- trash_vfolder --

    async def test_trash_vfolder_sets_delete_pending(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        ready_vfolder: uuid.UUID,
    ) -> None:
        updater = Updater(spec=VFolderTrashUpdaterSpec(), pk_value=ready_vfolder)
        result = await vfolder_repository.trash_vfolder(updater)

        assert result.id == ready_vfolder
        assert result.status == VFolderOperationStatus.DELETE_PENDING

    async def test_trash_vfolder_not_found(
        self,
        vfolder_repository: VfolderRepository,
    ) -> None:
        updater = Updater(spec=VFolderTrashUpdaterSpec(), pk_value=uuid.uuid4())
        with pytest.raises(VFolderNotFound):
            await vfolder_repository.trash_vfolder(updater)

    # -- restore_vfolders_from_trash --

    async def test_restore_sets_ready(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        ready_vfolder: uuid.UUID,
    ) -> None:
        """Trash then restore -> status back to READY."""
        # First trash it
        updater = Updater(spec=VFolderTrashUpdaterSpec(), pk_value=ready_vfolder)
        trashed = await vfolder_repository.trash_vfolder(updater)
        assert trashed.status == VFolderOperationStatus.DELETE_PENDING

        # Now restore
        restored = await vfolder_repository.restore_vfolders_from_trash([ready_vfolder])
        assert len(restored) == 1
        assert restored[0].id == ready_vfolder
        assert restored[0].status == VFolderOperationStatus.READY

    async def test_restore_nonexistent_returns_empty(
        self,
        vfolder_repository: VfolderRepository,
    ) -> None:
        result = await vfolder_repository.restore_vfolders_from_trash([uuid.uuid4()])
        assert result == []
