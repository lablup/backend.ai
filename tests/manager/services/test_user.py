import uuid
from datetime import datetime

import pytest

from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.users.type import UserCreator, UserData

from .test_utils import TestScenario


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Create a user",
            CreateUserAction(
                input=UserCreator(
                    email="test@lablup.com",
                    username="test",
                    password="password",
                    need_password_change=True,
                    domain_name="default",
                    full_name=None,
                    description=None,
                    is_active=None,
                    status=None,
                    role=None,
                    allowed_client_ip=None,
                    totp_activated=None,
                    resource_policy=None,
                    sudo_session_enabled=None,
                    group_ids=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
            ),
            CreateUserActionResult(
                data=UserData(
                    id=uuid.UUID("676fb4e3-17d3-48e9-91ca-4c94cde32a46"),
                    uuid=uuid.UUID("676fb4e3-17d3-48e9-91ca-4c94cde32a46"),
                    username="test",
                    email="test@lablup.com",
                    need_password_change=True,
                    full_name=None,
                    description=None,
                    is_active=True,
                    status="active",
                    status_info="admin-requested",
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    domain_name="default",
                    role="user",
                    resource_policy="default",
                    allowed_client_ip=None,
                    totp_activated=False,
                    totp_activated_at=None,
                    sudo_session_enabled=False,
                    main_access_key=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
                success=True,
            ),
        ),
        TestScenario.failure(
            "Create a user with duplicated email",
            CreateUserAction(
                input=UserCreator(
                    email="admin@lablup.com",
                    username="admin",
                    password="password",
                    need_password_change=True,
                    domain_name="default",
                    full_name=None,
                    description=None,
                    is_active=None,
                    status=None,
                    role=None,
                    allowed_client_ip=None,
                    totp_activated=None,
                    resource_policy=None,
                    sudo_session_enabled=None,
                    group_ids=None,
                    container_uid=None,
                    container_main_gid=None,
                    container_gids=None,
                ),
            ),
            ValueError,
        ),
    ],
)
async def test_create_user(
    processors: UserProcessors,
    test_scenario: TestScenario[CreateUserAction, CreateUserActionResult],
) -> None:
    await test_scenario.test(processors.create_user.wait_for_complete)
