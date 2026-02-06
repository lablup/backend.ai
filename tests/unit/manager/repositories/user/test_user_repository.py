"""
Tests for UserRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.user import UserConflict, UserCreationBadRequest, UserNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    PermissionGroupRow,
    PermissionRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestUserRepository:
    """Test cases for UserRepository using real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                RoleRow,  # RBAC role table
                PermissionGroupRow,  # Depends on RoleRow
                PermissionRow,  # Depends on PermissionGroupRow
                AssociationScopesEntitiesRow,  # RBAC scopes-entities association
                KeyPairRow,
                GroupRow,
                AssocGroupUserRow,  # Association table for users-groups
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def user_repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> UserRepository:
        """Create UserRepository instance with real database"""
        return UserRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test domain and return its name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def user_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a user resource policy and return its name."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def default_keypair_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create the default keypair resource policy and return its name."""
        policy_name = "default"
        async with db_with_cleanup.begin_session() as session:
            policy = KeyPairResourcePolicyRow(
                name=policy_name,
                total_resource_slots=ResourceSlot(),
                max_concurrent_sessions=10,
                max_session_lifetime=0,
                max_pending_session_count=5,
                max_pending_session_resource_slots=ResourceSlot(),
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=0,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def project_resource_policy(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a project resource policy and return its name."""
        policy_name = f"project-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def sample_user_email(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        user_resource_policy: str,
    ) -> str:
        """Create a test user and return the email."""
        email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=email,
                password=create_test_password_info("test_password"),
                need_password_change=False,
                full_name="Test User",
                description="Test Description",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=sample_domain,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
            )
            session.add(user)
            await session.commit()
        return email

    @pytest.fixture
    async def sample_user_username(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        user_resource_policy: str,
    ) -> str:
        """Create a test user and return the username."""
        username = f"testuser-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            user = UserRow(
                uuid=uuid.uuid4(),
                username=username,
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=create_test_password_info("test_password"),
                need_password_change=False,
                full_name="Test User",
                description="Test Description",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=sample_domain,
                role=UserRole.USER,
                resource_policy=user_resource_policy,
            )
            session.add(user)
            await session.commit()
        return username

    @pytest.fixture
    async def sample_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        project_resource_policy: str,
    ) -> str:
        """Create a test group and return its id as string."""
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=project_resource_policy,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.commit()
        return str(group_id)

    @pytest.mark.asyncio
    async def test_get_by_email_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_email: str,
    ) -> None:
        """Test successful user retrieval by email"""
        result = await user_repository.get_by_email_validated(sample_user_email)

        assert result is not None
        assert isinstance(result, UserData)
        assert result.email == sample_user_email
        assert result.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_get_by_email_validated_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test user retrieval when user not found"""
        with pytest.raises(UserNotFound):
            await user_repository.get_by_email_validated("nonexistent@example.com")

    @pytest.mark.asyncio
    async def test_create_user_validated_success(
        self,
        user_repository: UserRepository,
        sample_domain: str,
        user_resource_policy: str,
        default_keypair_resource_policy: str,
        sample_group_id: str,
    ) -> None:
        """Test successful user creation"""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username=f"newuser-{uuid.uuid4().hex[:8]}",
            email=f"newuser-{uuid.uuid4().hex[:8]}@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        result = await user_repository.create_user_validated(
            creator,
            group_ids=[sample_group_id],
        )

        assert result is not None
        assert result.user.email == spec.email
        assert result.user.username == spec.username
        assert result.user.role == spec.role
        assert result.keypair is not None
        assert result.keypair.access_key is not None

    @pytest.mark.asyncio
    async def test_create_user_validated_domain_not_exists(
        self,
        user_repository: UserRepository,
        user_resource_policy: str,
    ) -> None:
        """Test user creation fails when domain does not exist"""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username="newuser",
            email="newuser@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name="nonexistent-domain",
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        with pytest.raises(UserCreationBadRequest, match=r"Domain.*does not exist"):
            await user_repository.create_user_validated(creator, group_ids=[])

    @pytest.mark.asyncio
    async def test_create_user_validated_duplicate_email(
        self,
        user_repository: UserRepository,
        sample_user_email: str,
        sample_domain: str,
        user_resource_policy: str,
    ) -> None:
        """Test user creation fails when email already exists"""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username=f"different-{uuid.uuid4().hex[:8]}",
            email=sample_user_email,  # Same email as existing user
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        with pytest.raises(UserConflict, match=r"User with email.*or username.*already exists"):
            await user_repository.create_user_validated(creator, group_ids=[])

    @pytest.mark.asyncio
    async def test_create_user_validated_duplicate_username(
        self,
        user_repository: UserRepository,
        sample_user_username: str,
        sample_domain: str,
        user_resource_policy: str,
    ) -> None:
        """Test user creation fails when username already exists"""
        spec = UserCreatorSpec(
            username=sample_user_username,  # Same username as existing user
            email=f"different-{uuid.uuid4().hex[:8]}@example.com",
            password=create_test_password_info("new_password"),
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        with pytest.raises(UserConflict, match=r"User with email.*or username.*already exists"):
            await user_repository.create_user_validated(creator, group_ids=[])

    @pytest.fixture
    async def model_store_project_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        project_resource_policy: str,
    ) -> uuid.UUID:
        """Create a model store project and return its id."""
        project_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=project_id,
                name=f"model-store-{uuid.uuid4().hex[:8]}",
                description="Model Store Project",
                is_active=True,
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=project_resource_policy,
                type=ProjectType.MODEL_STORE,
            )
            session.add(group)
            await session.commit()
        return project_id

    async def test_create_user_validated_creates_domain_scope_association(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user_repository: UserRepository,
        sample_domain: str,
        user_resource_policy: str,
        default_keypair_resource_policy: str,
    ) -> None:
        """Test that user creation creates domain scope association via RBACEntityCreator."""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username=f"newuser-{uuid.uuid4().hex[:8]}",
            email=f"newuser-{uuid.uuid4().hex[:8]}@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        result = await user_repository.create_user_validated(creator, group_ids=[])

        # Verify domain scope association was created
        async with db_with_cleanup.begin_session() as session:
            domain_assoc = await session.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(result.user.uuid),
                    AssociationScopesEntitiesRow.scope_type == ScopeType.DOMAIN,
                    AssociationScopesEntitiesRow.scope_id == sample_domain,
                )
            )
            assert domain_assoc is not None

    async def test_create_user_validated_creates_project_scope_associations(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user_repository: UserRepository,
        sample_domain: str,
        user_resource_policy: str,
        default_keypair_resource_policy: str,
        sample_group_id: str,
    ) -> None:
        """Test that user creation creates project scope associations for requested groups."""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username=f"newuser-{uuid.uuid4().hex[:8]}",
            email=f"newuser-{uuid.uuid4().hex[:8]}@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        result = await user_repository.create_user_validated(creator, group_ids=[sample_group_id])

        # Verify project scope association was created
        async with db_with_cleanup.begin_session() as session:
            project_assoc = await session.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(result.user.uuid),
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == sample_group_id,
                )
            )
            assert project_assoc is not None

    async def test_create_user_validated_auto_includes_model_store_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user_repository: UserRepository,
        sample_domain: str,
        user_resource_policy: str,
        default_keypair_resource_policy: str,
        model_store_project_id: uuid.UUID,
    ) -> None:
        """Test that user creation automatically includes model store project in scope associations."""
        password_info = create_test_password_info("new_password")
        spec = UserCreatorSpec(
            username=f"newuser-{uuid.uuid4().hex[:8]}",
            email=f"newuser-{uuid.uuid4().hex[:8]}@example.com",
            password=password_info,
            need_password_change=False,
            full_name="New User",
            description="New User Description",
            status=UserStatus.ACTIVE,
            domain_name=sample_domain,
            role=UserRole.USER,
            resource_policy=user_resource_policy,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )
        creator = Creator(spec=spec)

        # Create user without explicitly specifying the model store project
        result = await user_repository.create_user_validated(creator, group_ids=[])

        # Verify model store project scope association was automatically created
        async with db_with_cleanup.begin_session() as session:
            model_store_assoc = await session.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.USER,
                    AssociationScopesEntitiesRow.entity_id == str(result.user.uuid),
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                    AssociationScopesEntitiesRow.scope_id == str(model_store_project_id),
                )
            )
            assert model_store_assoc is not None

            # Also verify user was added to the model store group
            group_assoc = await session.scalar(
                sa.select(AssocGroupUserRow).where(
                    AssocGroupUserRow.user_id == result.user.uuid,
                    AssocGroupUserRow.group_id == model_store_project_id,
                )
            )
            assert group_assoc is not None

    @pytest.mark.asyncio
    async def test_update_user_validated_success(
        self,
        user_repository: UserRepository,
        sample_user_email: str,
    ) -> None:
        """Test successful user update"""
        updater_spec = UserUpdaterSpec(
            full_name=OptionalState.update("Updated Name"),
            description=OptionalState.update("Updated Description"),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_user_email)

        result = await user_repository.update_user_validated(
            email=sample_user_email,
            updater=updater,
        )

        assert result is not None
        assert isinstance(result, UserData)
        assert result.full_name == "Updated Name"
        assert result.description == "Updated Description"

    @pytest.mark.asyncio
    async def test_update_user_validated_not_found(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test user update when user not found"""
        updater_spec = UserUpdaterSpec(
            full_name=OptionalState.update("Updated Name"),
        )
        updater = Updater(spec=updater_spec, pk_value="nonexistent@example.com")

        with pytest.raises(UserNotFound):
            await user_repository.update_user_validated(
                email="nonexistent@example.com",
                updater=updater,
            )

    @pytest.mark.asyncio
    async def test_soft_delete_user_validated_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user_repository: UserRepository,
        sample_user_email: str,
    ) -> None:
        """Test successful user soft deletion"""
        await user_repository.soft_delete_user_validated(email=sample_user_email)

        # Verify the user status is now DELETED
        async with db_with_cleanup.begin_session() as session:
            result = await session.scalar(
                sa.select(UserRow).where(UserRow.email == sample_user_email)
            )
            assert result is not None
            assert result.status == UserStatus.DELETED

    @pytest.mark.asyncio
    async def test_soft_delete_user_validated_nonexistent_user(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test soft delete for non-existent user succeeds silently (idempotent)"""
        # The method is idempotent - it doesn't raise an error for non-existent users
        await user_repository.soft_delete_user_validated(email="nonexistent@example.com")
        # No exception should be raised

    @pytest.mark.asyncio
    async def test_repository_has_expected_methods(
        self,
        user_repository: UserRepository,
    ) -> None:
        """Test that repository has expected methods"""
        assert hasattr(user_repository, "get_by_email_validated")
        assert hasattr(user_repository, "create_user_validated")
        assert hasattr(user_repository, "update_user_validated")
        assert hasattr(user_repository, "soft_delete_user_validated")


class TestUserDataConversion:
    """Tests for UserData conversion from UserRow"""

    def test_user_data_conversion(self) -> None:
        """Test UserData conversion from UserRow"""
        user_row = UserRow(
            uuid=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password="hashed_password",
            need_password_change=False,
            full_name="Test User",
            description="Test Description",
            status=UserStatus.ACTIVE,
            status_info="admin-requested",
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            allowed_client_ip=None,
            totp_activated=False,
            totp_activated_at=None,
            sudo_session_enabled=False,
            main_access_key="test_access_key",
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )

        user_data = UserData.from_row(user_row)

        assert user_data.uuid == user_row.uuid
        assert user_data.username == user_row.username
        assert user_data.email == user_row.email
        assert user_data.full_name == user_row.full_name
        assert user_data.role == user_row.role
        assert user_data.status == user_row.status
        assert user_data.domain_name == user_row.domain_name

    def test_user_status_validation(self) -> None:
        """Test user status validation"""
        valid_statuses = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.DELETED]
        for status in valid_statuses:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "status": status,
                "domain_name": "default",
                "role": UserRole.USER,
            }
            assert user_data["status"] in valid_statuses

    def test_user_role_validation(self) -> None:
        """Test user role validation"""
        valid_roles = [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.MONITOR]
        for role in valid_roles:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "role": role,
                "domain_name": "default",
                "status": UserStatus.ACTIVE,
            }
            assert user_data["role"] in valid_roles
