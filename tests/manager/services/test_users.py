import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.models.group import (
    AssocGroupUserRow,
    GroupRow,
    ProjectType,
)
from ai.backend.manager.models.keypair import (
    KeyPairRow,
    generate_keypair,
    generate_ssh_keypair,
    keypairs,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import DeleteUserAction
from ai.backend.manager.services.user.actions.modify_user import ModifyUserAction, UserModifier
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.services.user.type import UserCreator, UserData, UserInfoContext
from ai.backend.manager.types import OptionalState

from .test_utils import TestScenario


@pytest.fixture
def mock_redis_connection():
    mock_redis_connection = MagicMock(spec=ValkeyStatClient)
    return mock_redis_connection


@pytest.fixture
def mock_storage_manager():
    mock_storage_manager = MagicMock(spec=StorageSessionManager)
    return mock_storage_manager


@pytest.fixture
def mock_action_monitor():
    mock_action_monitor = MagicMock(spec=ActionMonitor)
    return mock_action_monitor


@pytest.fixture
def processors(
    database_fixture,
    database_engine,
    mock_storage_manager,
    mock_redis_connection,
    mock_action_monitor,
) -> UserProcessors:
    agent_registry_mock = MagicMock()
    user_service = UserService(
        db=database_engine,
        storage_manager=mock_storage_manager,
        valkey_stat_client=mock_redis_connection,
        agent_registry=agent_registry_mock,
    )
    return UserProcessors(user_service=user_service, action_monitors=[mock_action_monitor])


@pytest.fixture
def create_user(
    database_engine: ExtendedAsyncSAEngine,
    processors: UserProcessors,
):
    # NOTICE: To use 'default' resource policy, you must use `database_fixture` concurrently in test function
    @asynccontextmanager
    async def _create_user(
        email: str,
        name: str,
        domain_name: str,
        *,
        need_password_change: bool = False,
        role: UserRole = UserRole.USER,
        full_name: str = "Sample User",
        password: str = "sample_password",
        resource_policy_name: str = "default",
        description: str = "",
        totp_activated: bool = False,
        sudo_session_enabled: bool = False,
        is_active: bool = True,
    ) -> AsyncGenerator[uuid.UUID, None]:
        user_data = {
            "username": name,
            "password": password,
            "email": email,
            "need_password_change": need_password_change,
            "full_name": full_name,
            "domain_name": domain_name,
            "role": role,
            "status": UserStatus.ACTIVE,
            "allowed_client_ip": None,
            "resource_policy": resource_policy_name,
            "description": description,
            "totp_activated": totp_activated,
            "sudo_session_enabled": sudo_session_enabled,
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
                "is_active": is_active,
                "is_admin": role == UserRole.SUPERADMIN or role == UserRole.ADMIN,
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

            # Add user to groups if group_ids parameter is provided.
            if len(gids_to_join) > 0:
                query = (
                    sa.select(GroupRow.id)
                    .where(GroupRow.domain_name == domain_name)
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
                await session.execute(sa.delete(keypairs).where(keypairs.c.user_id == email))
                await session.execute(sa.delete(UserRow).where(UserRow.uuid == user_id))

    return _create_user


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "With valid data, create user action will be successful",
            CreateUserAction(
                input=UserCreator(
                    username="testuser",
                    password="password123",
                    email="test_user@test.com",
                    need_password_change=False,
                    domain_name="default",
                    full_name="Test User",
                    description="Test user description",
                    is_active=True,
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER,
                    allowed_client_ip=None,
                    totp_activated=False,
                    resource_policy="default",
                    sudo_session_enabled=False,
                    group_ids=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
            ),
            CreateUserActionResult(
                data=UserData(
                    id=uuid.uuid4(),
                    uuid=uuid.uuid4(),
                    username="testuser",
                    email="test_user@test.com",
                    need_password_change=False,
                    full_name="Test User",
                    description="Test user description",
                    is_active=True,
                    status=UserStatus.ACTIVE,
                    status_info="admin-requested",
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    domain_name="default",
                    role=UserRole.USER,
                    resource_policy="default",
                    allowed_client_ip=None,
                    totp_activated=False,
                    totp_activated_at=datetime.now(),
                    sudo_session_enabled=False,
                    main_access_key=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
                success=True,
            ),
        ),
        TestScenario.success(
            "With non-existing domain name, create user action will return result with None data",
            CreateUserAction(
                input=UserCreator(
                    username="test_user_not_existing_domain",
                    password="password123",
                    email="test@test.com",
                    need_password_change=False,
                    domain_name="non_existing_domain",
                    full_name="Test User",
                    description="Test user description",
                    is_active=True,
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER,
                    allowed_client_ip=None,
                    totp_activated=False,
                    resource_policy="default",
                    sudo_session_enabled=False,
                    group_ids=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
            ),
            CreateUserActionResult(
                data=None,
                success=False,
            ),
        ),
    ],
)
async def test_create_user(
    test_scenario: TestScenario,
    processors: UserProcessors,
) -> None:
    await test_scenario.test(processors.create_user.wait_for_complete)


async def test_create_default_keypair_after_create_user(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
    create_user,
) -> None:
    user_email = "test-keypair-create-user@email.com"
    async with create_user(email=user_email, name="test-user", domain_name="default") as user_id:
        async with database_engine.begin_session() as session:
            keypair = await session.scalar(
                sa.select(KeyPairRow).where((KeyPairRow.user == user_id))
            )

            assert keypair is not None
            assert keypair.is_active is True
            assert keypair.resource_policy == DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
            assert keypair.rate_limit == DEFAULT_KEYPAIR_RATE_LIMIT

            user_main_access_key = await session.scalar(
                sa.select(UserRow.main_access_key).where(UserRow.uuid == user_id)
            )

            assert user_main_access_key == keypair.access_key


async def test_create_user_join_model_store_project(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
    create_user,
) -> None:
    user_email = "test-join-model-store@email.com"
    async with create_user(email=user_email, name="test-user", domain_name="default") as user_id:
        async with database_engine.begin_session() as session:
            user_group_assoc = await session.scalar(
                sa.select(AssocGroupUserRow).where(AssocGroupUserRow.user_id == user_id)
            )

            assert user_group_assoc is not None
            assert user_group_assoc.group_id == uuid.UUID(
                "8e32dd28-d319-4e3b-8851-ea37837699a5"
            )  # fixture injected in root conftest


async def test_modify_user(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
    create_user,
) -> None:
    user_email = "modify-user@test.com"
    async with create_user(
        email=user_email,
        name="test",
        domain_name="default",
        role=UserRole.USER,
        full_name="Modify User",
        password="password123",
    ) as _:
        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                username=OptionalState.update("modify_user"),
                full_name=OptionalState.update("Modified User"),
                totp_activated=OptionalState.update(True),
                status=OptionalState.update(UserStatus.INACTIVE),
            ),
        )

        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None

        # Check if the user data is modified correctly
        assert result.data.full_name == "Modified User"
        assert result.data.totp_activated is True
        assert result.data.status == UserStatus.INACTIVE

        # Check if data not modified
        assert result.data.role == UserRole.USER
        assert result.data.status_info == "admin-requested"
        assert result.data.modified_at is not None
        assert result.data.resource_policy == "default"


async def test_modify_user_role_to_admin(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
    create_user,
) -> None:
    user_email = "modify-user-role@test.com"
    async with create_user(
        email=user_email,
        name="test",
        domain_name="default",
        role=UserRole.USER,
    ) as user_id:
        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                role=OptionalState.update(UserRole.ADMIN),
            ),
        )
        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None

        # Check if the user data is modified correctly
        assert result.data.role == UserRole.ADMIN

        # Check if keypair updated as active admin
        async with database_engine.begin_session() as session:
            keypair = await session.scalar(
                sa.select(KeyPairRow).where((KeyPairRow.user == user_id))
            )

            assert keypair is not None
            assert keypair.is_active is True
            assert keypair.is_admin is True


async def test_modify_admin_user_to_normal_user(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
    create_user,
) -> None:
    user_email = "modify-user-role@test.com"
    async with create_user(
        email=user_email,
        name="test",
        domain_name="default",
        role=UserRole.SUPERADMIN,
    ) as user_id:
        action = ModifyUserAction(
            email=user_email,
            modifier=UserModifier(
                role=OptionalState.update(UserRole.USER),
            ),
        )
        result = await processors.modify_user.wait_for_complete(action)

        assert result.success is True
        assert result.data is not None

        # Check if the user data is modified correctly
        assert result.data.role == UserRole.USER

        # Check if keypair updated as active but not admin
        async with database_engine.begin_session() as session:
            keypair = await session.scalar(
                sa.select(KeyPairRow).where((KeyPairRow.user == user_id))
            )

            assert keypair is not None
            assert keypair.is_active is True
            assert keypair.is_admin is False


@pytest.mark.asyncio
async def test_delete_user_success(
    processors: UserProcessors, database_engine: ExtendedAsyncSAEngine, create_user
) -> None:
    delete_user_email = "test-delete-user@email.com"
    async with create_user(
        email=delete_user_email, name="test-delete-user", domain_name="default"
    ) as user_id:
        delete_action = DeleteUserAction(email=delete_user_email)
        result = await processors.delete_user.wait_for_complete(delete_action)
        assert result.success is True

        # Check if the user and user keypair both deleted
        async with database_engine.begin_session() as session:
            result = await session.scalar(
                sa.select(KeyPairRow.is_active).where(KeyPairRow.user_id == delete_user_email)
            )
            assert result is False

            result = await session.scalar(
                sa.select(UserRow).where(
                    (UserRow.uuid == user_id) & (UserRow.status == UserStatus.ACTIVE)
                )
            )
            assert result is None

            result = await session.scalar(
                sa.select(UserRow).where(
                    (UserRow.uuid == user_id) & (UserRow.status == UserStatus.DELETED)
                )
            )
            assert result is not None


@pytest.mark.asyncio
async def test_purge_user(
    processors: UserProcessors, database_engine: ExtendedAsyncSAEngine, create_user, mocker
) -> None:
    delete_user_email = "test-delete-user@email.com"

    # No need to patch since mock_redis_connection now has the correct spec

    async with create_user(
        email=delete_user_email, name="test-delete-user", domain_name="default"
    ) as user_id:
        delete_action = DeleteUserAction(email=delete_user_email)
        result = await processors.delete_user.wait_for_complete(delete_action)

        async with database_engine.begin() as conn:
            main_access_key = await conn.scalar(
                sa.select(UserRow.main_access_key).where(UserRow.uuid == user_id)
            )

        purge_action = PurgeUserAction(
            email=delete_user_email,
            user_info_ctx=UserInfoContext(
                uuid=user_id,
                email=delete_user_email,
                main_access_key=main_access_key,
            ),
        )

        await processors.purge_user.wait_for_complete(purge_action)

        # Check if the user is purged
        async with database_engine.begin() as conn:
            result = await conn.scalar(sa.select(UserRow).where((UserRow.uuid == user_id)))
            assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.failure(
            "With non-existing email, purge user action will raise error",
            PurgeUserAction(
                email="non-exisiting-user@email.com",
                user_info_ctx=UserInfoContext(
                    uuid=uuid.UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                    email="non-exisiting-user@email.com",
                    main_access_key=AccessKey("sample_access_key"),
                ),
            ),
            RuntimeError,
        ),
    ],
)
async def test_purge_user_fail(
    processors: UserProcessors,
    test_scenario,
) -> None:
    await test_scenario.test(processors.purge_user.wait_for_complete)
