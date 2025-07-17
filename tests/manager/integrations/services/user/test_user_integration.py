"""
Integration tests for User Service functionality.
Tests the complete user service with real database connections and processors.
"""

import uuid
from typing import Any, AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.user.types import UserCreator, UserInfoContext
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow, ProjectType
from ai.backend.manager.models.keypair import (
    generate_keypair,
    generate_ssh_keypair,
    keypairs,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    UserModifier,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.types import OptionalState


@pytest.fixture
async def created_user(
    database_engine: ExtendedAsyncSAEngine,
    processors: UserProcessors,
) -> AsyncGenerator[uuid.UUID, None]:
    """
    Fixture that creates a user and yields the user ID.
    """
    # Generate unique identifiers
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"testuser-{unique_suffix}@example.com"
    name = f"testuser-{unique_suffix}"

    user_data = {
        "username": name,
        "password": "sample_password",
        "email": email,
        "need_password_change": False,
        "full_name": "Sample User",
        "domain_name": "default",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
        "allowed_client_ip": None,
        "resource_policy": "default",
        "description": "",
        "totp_activated": False,
        "sudo_session_enabled": False,
        "container_uid": None,
        "container_main_gid": None,
        "container_gids": None,
    }

    async with database_engine.begin_session() as session:
        await session.execute(sa.insert(UserRow).values(user_data))
        user_id = await session.scalar(sa.select(UserRow.uuid).where(UserRow.email == email))

        ak, sk = generate_keypair()
        pubkey, privkey = generate_ssh_keypair()
        kp_data = {
            "user_id": email,
            "access_key": ak,
            "secret_key": sk,
            "is_active": True,
            "is_admin": False,
            "resource_policy": DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
            "rate_limit": DEFAULT_KEYPAIR_RATE_LIMIT,
            "num_queries": 0,
            "ssh_public_key": pubkey,
            "ssh_private_key": privkey,
        }
        await session.execute(
            sa.insert(keypairs).values(
                **kp_data,
                user=user_id,
            )
        )
        await session.execute(
            sa.update(UserRow).where(UserRow.uuid == user_id).values(main_access_key=ak)
        )

        model_store_project = await session.scalar(
            sa.select(GroupRow).where(GroupRow.type == ProjectType.MODEL_STORE)
        )
        gids_to_join = [model_store_project.id] if model_store_project is not None else []

        if len(gids_to_join) > 0:
            query = (
                sa.select(GroupRow.id)
                .where(GroupRow.domain_name == "default")
                .where(GroupRow.id.in_(gids_to_join))
            )
            grps = (await session.execute(query)).all()
            if grps:
                group_data = [{"user_id": user_id, "group_id": grp.id} for grp in grps]
                group_insert_query = sa.insert(AssocGroupUserRow).values(group_data)
                await session.execute(group_insert_query)

    try:
        yield user_id
    finally:
        async with database_engine.begin_session() as session:
            await session.execute(
                sa.delete(AssocGroupUserRow).where(AssocGroupUserRow.user_id == user_id)
            )
            await session.execute(sa.delete(keypairs).where(keypairs.c.user == user_id))
            await session.execute(sa.delete(UserRow).where(UserRow.uuid == user_id))


class TestCreateUserIntegration:
    """Integration tests for Create User functionality"""

    async def test_create_user_normal(
        self,
        processors: UserProcessors,
        database_fixture: Any,
    ) -> None:
        """Test 1.1: Normal user creation with all required fields"""
        action = CreateUserAction(
            creator=UserCreator(
                email="testnewuser@example.com",
                password="SecurePass123!",
                username="testnewuser",
                full_name="New User",
                role=UserRole.USER,
                domain_name="default",
                need_password_change=False,
                resource_policy="default",
                status=UserStatus.ACTIVE,
                sudo_session_enabled=False,
            ),
        )

        result = await processors.create_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.email == "testnewuser@example.com"
        assert result.data.username == "testnewuser"
        assert result.data.full_name == "New User"
        assert result.data.role == UserRole.USER
        assert result.data.domain_name == "default"
        assert result.data.status == UserStatus.ACTIVE

    async def test_create_user_admin_with_sudo(
        self,
        processors: UserProcessors,
        database_fixture: Any,
    ) -> None:
        """Test 1.2: Admin user creation with sudo session enabled"""
        action = CreateUserAction(
            creator=UserCreator(
                email="testadmin@example.com",
                password="AdminPass123!",
                username="testadmin",
                full_name="Admin User",
                role=UserRole.ADMIN,
                domain_name="default",
                need_password_change=False,
                resource_policy="default",
                sudo_session_enabled=True,
            ),
        )

        result = await processors.create_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.email == "testadmin@example.com"
        assert result.data.role == UserRole.ADMIN
        assert result.data.sudo_session_enabled is True

    async def test_create_user_container_config(
        self,
        processors: UserProcessors,
        database_fixture: Any,
    ) -> None:
        """Test 1.5: Container UID/GID configuration"""
        action = CreateUserAction(
            creator=UserCreator(
                email="testcontainer@example.com",
                password="ContainerPass123!",
                username="testcontaineruser",
                need_password_change=False,
                domain_name="default",
                resource_policy="default",
                sudo_session_enabled=False,
                container_uid=2000,
                container_main_gid=2000,
                container_gids=[2000, 2001],
            ),
        )

        result = await processors.create_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.container_uid == 2000
        assert result.data.container_main_gid == 2000
        assert result.data.container_gids == [2000, 2001]

    async def test_create_user_resource_policy_and_ip_restriction(
        self,
        processors: UserProcessors,
        database_fixture: Any,
    ) -> None:
        """Test 1.6: Resource policy and IP restriction"""
        action = CreateUserAction(
            creator=UserCreator(
                email="testlimited@example.com",
                password="LimitedPass123!",
                username="testlimiteduser",
                need_password_change=False,
                domain_name="default",
                resource_policy="default",
                allowed_client_ip=["192.168.1.0/24"],
                sudo_session_enabled=False,
            ),
        )

        result = await processors.create_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.resource_policy == "default"
        assert result.data.allowed_client_ip is not None
        assert str(result.data.allowed_client_ip[0]) == "192.168.1.0/24"


class TestModifyUserIntegration:
    """Integration tests for Modify User functionality"""

    async def test_modify_user_basic_info(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test 2.1: Basic information modification"""
        # Get the created user's email
        async with database_engine.begin_session() as session:
            user_email = await session.scalar(
                sa.select(UserRow.email).where(UserRow.uuid == created_user)
            )

        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                full_name=OptionalState.update("Updated Name"),
                description=OptionalState.update("Senior Developer"),
            ),
        )

        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.full_name == "Updated Name"
        assert result.data.description == "Senior Developer"

    async def test_modify_user_role_elevation(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test 2.2: Permission elevation to admin"""
        # Get the created user's email
        async with database_engine.begin_session() as session:
            user_email = await session.scalar(
                sa.select(UserRow.email).where(UserRow.uuid == created_user)
            )

        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                role=OptionalState.update(UserRole.ADMIN),
            ),
        )

        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.role == UserRole.ADMIN

    async def test_modify_user_group_changes(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test 2.3: Group membership changes when domain changes"""
        user_id = created_user

        # Get the created user's email
        async with database_engine.begin_session() as session:
            user_email = await session.scalar(
                sa.select(UserRow.email).where(UserRow.uuid == user_id)
            )

        # Create a new domain
        async with database_engine.begin_session() as session:
            from ai.backend.manager.models.domain import DomainRow

            await session.execute(
                sa.insert(DomainRow).values({
                    "name": "test-domain",
                    "description": "Test domain for group changes",
                    "is_active": True,
                    "total_resource_slots": {},
                    "allowed_vfolder_hosts": {},
                })
            )

        # Create test groups in the new domain
        async with database_engine.begin_session() as session:
            new_team_id = uuid.uuid4()
            research_team_id = uuid.uuid4()

            await session.execute(
                sa.insert(GroupRow).values([
                    {
                        "id": new_team_id,
                        "name": "new-team",
                        "domain_name": "test-domain",
                        "type": ProjectType.GENERAL,
                        "resource_policy": "default",
                    },
                    {
                        "id": research_team_id,
                        "name": "research-team",
                        "domain_name": "test-domain",
                        "type": ProjectType.GENERAL,
                        "resource_policy": "default",
                    },
                ])
            )

        # Modify user to change domain and set groups
        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                domain_name=OptionalState.update("test-domain"),
            ),
            group_ids=[str(new_team_id), str(research_team_id)],
        )

        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None
        assert result.data.domain_name == "test-domain"

        # Verify group membership
        async with database_engine.begin_session() as session:
            user_groups = await session.execute(
                sa.select(AssocGroupUserRow.group_id).where(AssocGroupUserRow.user_id == user_id)
            )
            group_ids = [row[0] for row in user_groups]

            assert new_team_id in group_ids
            assert research_team_id in group_ids


class TestDeleteUserIntegration:
    """Integration tests for Delete User functionality"""

    async def test_delete_user_normal(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test 3.1: Normal user deletion"""
        user_id = created_user

        # Get the created user's email
        async with database_engine.begin_session() as session:
            user_email = await session.scalar(
                sa.select(UserRow.email).where(UserRow.uuid == user_id)
            )

        action = DeleteUserAction(email=user_email)
        result = await processors.delete_user.wait_for_complete(action)

        assert result.success is True

        # Verify user is soft deleted
        async with database_engine.begin_session() as session:
            user = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            assert user is not None
            assert user.status == UserStatus.DELETED


class TestPurgeUserIntegration:
    """Integration tests for Purge User functionality"""

    async def test_purge_user_complete(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test 4.1: Complete user purge"""
        user_id = created_user

        # Get the created user's email
        async with database_engine.begin_session() as session:
            user_email = await session.scalar(
                sa.select(UserRow.email).where(UserRow.uuid == user_id)
            )

        # First soft delete the user
        delete_action = DeleteUserAction(email=user_email)
        await processors.delete_user.wait_for_complete(delete_action)

        # Get main access key for purge action
        async with database_engine.begin_session() as session:
            main_access_key = await session.scalar(
                sa.select(UserRow.main_access_key).where(UserRow.uuid == user_id)
            )

        # Now purge
        purge_action = PurgeUserAction(
            email=user_email,
            user_info_ctx=UserInfoContext(
                uuid=user_id,
                email=user_email,
                main_access_key=AccessKey(main_access_key),
            ),
        )

        result = await processors.purge_user.wait_for_complete(purge_action)

        assert result.success is True

        # Verify user is completely removed
        async with database_engine.begin_session() as session:
            user = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            assert user is None


class TestUserStatsIntegration:
    """Integration tests for User Statistics functionality"""

    @pytest.mark.skip(
        reason="Stats tests require real ValkeyStatClient - skipping for integration tests"
    )
    async def test_user_month_stats_current_month(
        self,
        processors: UserProcessors,
        created_user: uuid.UUID,
    ) -> None:
        """Test 5.1: Normal statistics retrieval for current month"""
        user_id = created_user

        action = UserMonthStatsAction(
            user_id=str(user_id),
        )

        result = await processors.user_month_stats.wait_for_complete(action)

        assert isinstance(result, UserMonthStatsActionResult)
        assert result.stats is not None
        # The stats will be an empty list since we don't have any kernel data in the test DB
        assert isinstance(result.stats, list)

    @pytest.mark.skip(
        reason="Stats tests require real ValkeyStatClient - skipping for integration tests"
    )
    async def test_admin_month_stats_all_system(
        self,
        processors: UserProcessors,
    ) -> None:
        """Test 6.1: System-wide statistics"""
        action = AdminMonthStatsAction()

        result = await processors.admin_month_stats.wait_for_complete(action)

        assert isinstance(result, AdminMonthStatsActionResult)
        assert result.stats is not None
        # The stats will be an empty list since we don't have any kernel data in the test DB
        assert isinstance(result.stats, list)
