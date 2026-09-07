"""``BulkOwnCheck.held`` is the one place the caller's bits on named entities come from."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.actions.v2.bulk.validator.rbac import BulkOwnCheck
from ai.backend.manager.data.permission.virtual_entity import OwnCheckKey
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)


def _user(role: UserRole) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role is UserRole.SUPERADMIN,
        is_superadmin=role is UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


def _config(*, enforcement_enabled: bool) -> MagicMock:
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = enforcement_enabled
    return config_provider


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=PermissionControllerRepository)


@pytest.fixture
def entities() -> list[AgentUUID]:
    return [AgentUUID(uuid.uuid4()), AgentUUID(uuid.uuid4())]


async def test_superadmin_holds_everything(
    repository: AsyncMock, entities: list[AgentUUID]
) -> None:
    check = BulkOwnCheck(repository, _config(enforcement_enabled=True))

    with with_user(_user(UserRole.SUPERADMIN)):
        held = await check.held(entities)

    assert held == dict.fromkeys(entities, Permission.full())
    repository.owned_permissions.assert_not_awaited()


async def test_enforcement_off_holds_everything(
    repository: AsyncMock, entities: list[AgentUUID]
) -> None:
    check = BulkOwnCheck(repository, _config(enforcement_enabled=False))

    with with_user(_user(UserRole.USER)):
        held = await check.held(entities)

    assert held == dict.fromkeys(entities, Permission.full())
    repository.owned_permissions.assert_not_awaited()


async def test_a_user_holds_what_the_own_check_answers(
    repository: AsyncMock, entities: list[AgentUUID]
) -> None:
    user = _user(UserRole.USER)
    reached, unreached = entities
    repository.owned_permissions.return_value = {
        OwnCheckKey(user_id=UserID(user.user_id), entity=reached): Permission.READ,
    }
    check = BulkOwnCheck(repository, _config(enforcement_enabled=True))

    with with_user(user):
        held = await check.held(entities)

    # An entity nothing reaches holds NONE rather than being absent.
    assert held == {reached: Permission.READ, unreached: Permission.NONE}


async def test_missing_user_raises(repository: AsyncMock, entities: list[AgentUUID]) -> None:
    check = BulkOwnCheck(repository, _config(enforcement_enabled=True))

    with pytest.raises(UnreachableError):
        await check.held(entities)
