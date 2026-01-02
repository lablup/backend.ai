"""
Tests for AppConfigRepository functionality.
Tests the repository layer with real database and cache operations.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import BinarySize, ValkeyTarget
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.app_config import AppConfigRow, AppConfigScopeType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config import AppConfigRepository
from ai.backend.manager.repositories.app_config.creators import AppConfigCreatorSpec
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


def create_test_password_info(password: str) -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestAppConfigRepository:
    """Test cases for AppConfigRepository"""

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
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                AppConfigRow,
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
                description="Test domain for app config",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[str, None]:
        """Create test user and return user UUID string"""
        user_uuid = uuid.uuid4()
        user_id = str(user_uuid)

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=create_test_password_info("test_password"),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_id

    @pytest.fixture
    async def valkey_stat_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=0,
            human_readable_name="test-valkey-stat",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def app_config_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_stat_client: ValkeyStatClient,
    ) -> AsyncGenerator[AppConfigRepository, None]:
        """Create AppConfigRepository instance with real database and cache"""
        repo = AppConfigRepository(db=db_with_cleanup, valkey_stat=valkey_stat_client)
        yield repo

    @pytest.mark.asyncio
    async def test_create_domain_config(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
    ) -> None:
        """Test creating domain-level configuration"""
        creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark", "language": "en"},
            )
        )

        config = await app_config_repository.create_config(creator)

        assert config.scope_type == AppConfigScopeType.DOMAIN
        assert config.scope_id == test_domain_name
        assert config.extra_config == {"theme": "dark", "language": "en"}

    @pytest.mark.asyncio
    async def test_create_user_config(
        self,
        app_config_repository: AppConfigRepository,
        test_user_id: str,
    ) -> None:
        """Test creating user-level configuration"""
        creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.USER,
                scope_id=test_user_id,
                extra_config={"theme": "light", "notifications": True},
            )
        )

        config = await app_config_repository.create_config(creator)

        assert config.scope_type == AppConfigScopeType.USER
        assert config.scope_id == test_user_id
        assert config.extra_config == {"theme": "light", "notifications": True}

    @pytest.mark.asyncio
    async def test_get_merged_config_domain_only(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
        test_user_id: str,
    ) -> None:
        """Test getting merged config with only domain-level config"""
        # Create domain config
        domain_creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark", "language": "en"},
            )
        )
        await app_config_repository.create_config(domain_creator)

        # Get merged config
        merged_config = await app_config_repository.get_merged_config(test_user_id)

        assert merged_config == {"theme": "dark", "language": "en"}

    @pytest.mark.asyncio
    async def test_get_merged_config_with_user_override(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
        test_user_id: str,
    ) -> None:
        """Test getting merged config with user config overriding domain config"""
        # Create domain config
        domain_creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark", "language": "en", "sidebar": "expanded"},
            )
        )
        await app_config_repository.create_config(domain_creator)

        # Create user config that overrides theme
        user_creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.USER,
                scope_id=test_user_id,
                extra_config={"theme": "light", "notifications": True},
            )
        )
        await app_config_repository.create_config(user_creator)

        # Get merged config
        merged_config = await app_config_repository.get_merged_config(test_user_id)

        # User config should override domain config for 'theme'
        assert merged_config["theme"] == "light"  # Overridden by user
        assert merged_config["language"] == "en"  # From domain
        assert merged_config["sidebar"] == "expanded"  # From domain
        assert merged_config["notifications"] is True  # From user only

    @pytest.mark.asyncio
    async def test_upsert_config_create(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
    ) -> None:
        """Test upserting config when it doesn't exist (create)"""
        spec = AppConfigUpdaterSpec(
            extra_config=OptionalState.update({"theme": "dark", "language": "en"})
        )

        config = await app_config_repository.upsert_config(
            AppConfigScopeType.DOMAIN, test_domain_name, spec
        )

        assert config.scope_type == AppConfigScopeType.DOMAIN
        assert config.scope_id == test_domain_name
        assert config.extra_config == {"theme": "dark", "language": "en"}

    @pytest.mark.asyncio
    async def test_upsert_config_update(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
    ) -> None:
        """Test upserting config when it exists (update)"""
        # Create initial config
        creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark", "language": "en"},
            )
        )
        initial_config = await app_config_repository.create_config(creator)

        # Update config
        spec = AppConfigUpdaterSpec(
            extra_config=OptionalState.update({"theme": "light", "language": "ko"})
        )
        updated_config = await app_config_repository.upsert_config(
            AppConfigScopeType.DOMAIN, test_domain_name, spec
        )

        assert updated_config.id == initial_config.id
        assert updated_config.extra_config == {"theme": "light", "language": "ko"}

    @pytest.mark.asyncio
    async def test_delete_config(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
    ) -> None:
        """Test deleting configuration"""
        # Create config
        creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark"},
            )
        )
        await app_config_repository.create_config(creator)

        # Delete config
        deleted = await app_config_repository.delete_config(
            AppConfigScopeType.DOMAIN, test_domain_name
        )

        assert deleted is True

        # Verify deletion
        config = await app_config_repository.get_config(AppConfigScopeType.DOMAIN, test_domain_name)
        assert config is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
    ) -> None:
        """Test deleting non-existent configuration"""
        deleted = await app_config_repository.delete_config(
            AppConfigScopeType.DOMAIN, test_domain_name
        )

        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_merged_config_empty(
        self,
        app_config_repository: AppConfigRepository,
        test_user_id: str,
    ) -> None:
        """Test getting merged config when no config exists"""
        merged_config = await app_config_repository.get_merged_config(test_user_id)

        assert merged_config == {}

    @pytest.mark.asyncio
    async def test_cache_invalidation_domain_config(
        self,
        app_config_repository: AppConfigRepository,
        test_domain_name: str,
        test_user_id: str,
    ) -> None:
        """Test cache invalidation when domain config is updated"""
        # Create domain config
        domain_creator = Creator(
            spec=AppConfigCreatorSpec(
                scope_type=AppConfigScopeType.DOMAIN,
                scope_id=test_domain_name,
                extra_config={"theme": "dark"},
            )
        )
        await app_config_repository.create_config(domain_creator)

        # First call - cache miss, fetch from DB
        merged_config1 = await app_config_repository.get_merged_config(test_user_id)
        assert merged_config1 == {"theme": "dark"}

        # Second call - cache hit
        merged_config2 = await app_config_repository.get_merged_config(test_user_id)
        assert merged_config2 == {"theme": "dark"}

        # Update domain config - should invalidate cache
        spec = AppConfigUpdaterSpec(extra_config=OptionalState.update({"theme": "light"}))
        await app_config_repository.upsert_config(AppConfigScopeType.DOMAIN, test_domain_name, spec)

        # Cache should be invalidated, get updated config
        merged_config3 = await app_config_repository.get_merged_config(test_user_id)
        assert merged_config3 == {"theme": "light"}
