import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AccessKey, RedisConnectionInfo
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.keypair import keypairs
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
    mock_redis_connection = MagicMock(spec=RedisConnectionInfo)
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
    user_service = UserService(
        db=database_engine, storage_manager=mock_storage_manager, redis_stat=mock_redis_connection
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
        create_user_action = CreateUserAction(
            UserCreator(
                username=name,
                password=password,
                email=email,
                need_password_change=need_password_change,
                full_name=full_name,
                domain_name=domain_name,
                is_active=is_active,
                role=role,
                status=UserStatus.ACTIVE,
                allowed_client_ip=None,
                group_ids=None,
                resource_policy=resource_policy_name,
                description=description,
                totp_activated=totp_activated,
                sudo_session_enabled=sudo_session_enabled,
                container_uid=None,
                container_main_gid=None,
                container_gids=None,
            ),
        )
        result: CreateUserActionResult = await processors.create_user.wait_for_complete(
            create_user_action
        )
        assert result.data is not None
        user_id = result.data.id

        try:
            yield user_id

        finally:
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(keypairs).where(keypairs.c.user_id == email))
                await session.execute(sa.delete(UserRow).where(UserRow.uuid == user_id))

    return _create_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Create user with valid data",
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
            "Try to create user with non exsiting domain",
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


@pytest.mark.asyncio
async def test_modify_user(
    processors: UserProcessors,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    create_user_action = CreateUserAction(
        input=UserCreator(
            username="modify-user",
            password="password123",
            email="modify-user@test.com",
            need_password_change=False,
            full_name="Modify User",
            domain_name="default",
            role=UserRole.USER,
            resource_policy="default",
            status=UserStatus.ACTIVE,
            description="Test user description",
            is_active=True,
            allowed_client_ip=None,
            totp_activated=False,
            sudo_session_enabled=False,
            group_ids=None,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        ),
    )
    create_result = await processors.create_user.wait_for_complete(create_user_action)
    user_data = create_result.data
    assert user_data is not None
    user_id = user_data.id

    async with database_engine.begin() as conn:
        keypair_result = await conn.scalar(
            sa.select([
                keypairs.c.user,
                keypairs.c.is_active,
                keypairs.c.is_admin,
                keypairs.c.access_key,
            ])
            .select_from(keypairs)
            .where(keypairs.c.user == user_id)
            .order_by(sa.desc(keypairs.c.is_admin))
            .order_by(sa.desc(keypairs.c.is_active)),
        )
        assert keypair_result is not None

    action = ModifyUserAction(
        email="modify-user@test.com",
        modifier=UserModifier(
            username=OptionalState.update("modify_user"),
            domain_name=OptionalState.update("default"),
            full_name=OptionalState.update("Modified User"),
            totp_activated=OptionalState.update(True),
            role=OptionalState.update(UserRole.ADMIN),
        ),
    )

    result = await processors.modify_user.wait_for_complete(action)

    assert result.success is True
    assert result.data is not None

    # Check if the user data is modified correctly
    assert result.data.full_name == "Modified User"
    assert result.data.totp_activated is True
    assert result.data.role == UserRole.ADMIN

    # Check if data not modified
    assert result.data.status_info == "admin-requested"
    assert result.data.modified_at is not None
    assert result.data.resource_policy == "default"


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

        # Check if the user is deleted
        async with database_engine.begin() as conn:
            result = await conn.scalar(
                sa.select(keypairs.c.is_active).where(keypairs.c.user_id == delete_user_email)
            )
            assert result == False  # noqa

            result = await conn.scalar(
                sa.select(UserRow).where(
                    (UserRow.uuid == user_id) & (UserRow.status == UserStatus.ACTIVE)
                )
            )
            assert result is None

            result = await conn.scalar(
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

    async def mock_execute(*args, **kwargs):
        return None

    mocker.patch("ai.backend.common.redis_helper.execute", side_effect=mock_execute)

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
            "test purge user with non-existing email",
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
