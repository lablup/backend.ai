"""The gate of the global layer: the role bypasses, then the `global` singleton's bits.

The permission read is stubbed here so the keys the gate asks with, and what it does
with the answer, are pinned on their own. The graph behind the answer is exercised in
the component test that grants a role through the product paths.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.global_scope.validator.rbac import (
    VirtualEntityGlobalActionRBACValidator,
)
from ai.backend.manager.actions.v2.global_scope.validator.refusing import (
    RefusingGlobalActionValidator,
)
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache, global_entity_id
from ai.backend.manager.data.permission.virtual_entity import GovernCheckKey
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)


@dataclass
class _SearchAction(BaseGlobalAction):
    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return ResourceSlotTypeEntityType()

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @classmethod
    @override
    def action_name(cls) -> str:
        return "search_things"


@dataclass
class _CreateAction(_SearchAction):
    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "create_thing"


@dataclass
class _Result:
    pass


async def _run(_: _SearchAction) -> _Result:
    return _Result()


def _user(role: UserRole = UserRole.USER) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def global_singleton() -> Iterator[GlobalEntityID]:
    ids = {name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName}
    GlobalEntityIDCache.fill(ids)
    try:
        yield ids[GlobalEntityName.GLOBAL]
    finally:
        GlobalEntityIDCache.clear()


def _config_provider(*, enforcement_enabled: bool = True) -> MagicMock:
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = enforcement_enabled
    return config_provider


def _repository(granted: Permission) -> MagicMock:
    repository = MagicMock(spec=RbacPermissionCheckRepository)
    repository.governed_permissions = AsyncMock(
        side_effect=lambda keys: dict.fromkeys(keys, granted)
    )
    return repository


def _processor(
    repository: MagicMock,
    config_provider: MagicMock,
) -> GlobalActionProcessor[_SearchAction, _Result]:
    return GlobalActionProcessor(
        _run,
        validators=[VirtualEntityGlobalActionRBACValidator(repository, config_provider)],
    )


class TestTheGateIsStated:
    def test_a_processor_without_a_validator_is_refused(self) -> None:
        with pytest.raises(ServerMisconfiguredError):
            GlobalActionProcessor[_SearchAction, _Result](_run)

        with pytest.raises(ServerMisconfiguredError):
            GlobalActionProcessor[_SearchAction, _Result](_run, validators=[])

    async def test_the_refusing_validator_lets_no_one_through(self) -> None:
        processor = GlobalActionProcessor[_SearchAction, _Result](
            _run, validators=[RefusingGlobalActionValidator()]
        )

        with with_user(_user(UserRole.SUPERADMIN)):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_SearchAction())


class TestRoleBypasses:
    async def test_a_superadmin_passes_without_a_permission_read(self) -> None:
        repository = _repository(Permission.NONE)
        processor = _processor(repository, _config_provider())

        with with_user(_user(UserRole.SUPERADMIN)):
            assert isinstance(await processor.run(_SearchAction()), _Result)

        repository.governed_permissions.assert_not_awaited()

    async def test_a_monitor_passes_a_read_without_a_permission_read(self) -> None:
        repository = _repository(Permission.NONE)
        processor = _processor(repository, _config_provider())

        with with_user(_user(UserRole.MONITOR)):
            assert isinstance(await processor.run(_SearchAction()), _Result)

        repository.governed_permissions.assert_not_awaited()

    async def test_a_monitor_is_refused_anything_but_a_read(
        self, global_singleton: GlobalEntityID
    ) -> None:
        processor = _processor(_repository(Permission.NONE), _config_provider())

        with with_user(_user(UserRole.MONITOR)):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_CreateAction())


class TestGlobalSingletonPermission:
    async def test_the_granted_user_passes(self, global_singleton: GlobalEntityID) -> None:
        processor = _processor(_repository(Permission.READ), _config_provider())

        with with_user(_user()):
            assert isinstance(await processor.run(_SearchAction()), _Result)

    async def test_the_user_holding_nothing_is_refused(
        self, global_singleton: GlobalEntityID
    ) -> None:
        processor = _processor(_repository(Permission.NONE), _config_provider())

        with with_user(_user()):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_SearchAction())

    async def test_read_does_not_carry_a_write(self, global_singleton: GlobalEntityID) -> None:
        processor = _processor(_repository(Permission.READ), _config_provider())

        with with_user(_user()):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_CreateAction())

    async def test_the_key_names_the_singleton_and_the_action_type(
        self, global_singleton: GlobalEntityID
    ) -> None:
        repository = _repository(Permission.READ)
        processor = _processor(repository, _config_provider())
        user = _user()

        with with_user(user):
            await processor.run(_SearchAction())

        (keys,) = repository.governed_permissions.await_args.args
        assert list(keys) == [
            GovernCheckKey(
                user_id=UserID(user.user_id),
                scope=global_singleton,
                entity_type=ResourceSlotTypeEntityType(),
            )
        ]

    async def test_another_types_grant_does_not_reach_this_one(
        self, global_singleton: GlobalEntityID
    ) -> None:
        repository = MagicMock(spec=RbacPermissionCheckRepository)
        user_type_only = {
            GovernCheckKey(
                user_id=UserID(uuid.uuid4()),
                scope=global_entity_id(GlobalEntityName.GLOBAL),
                entity_type=UserEntityType(),
            ): Permission.READ
        }
        repository.governed_permissions = AsyncMock(
            side_effect=lambda keys: {key: user_type_only.get(key, Permission.NONE) for key in keys}
        )
        processor = _processor(repository, _config_provider())

        with with_user(_user()):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_SearchAction())


class TestEnforcementOff:
    async def test_a_superadmin_still_passes(self) -> None:
        processor = _processor(
            _repository(Permission.NONE), _config_provider(enforcement_enabled=False)
        )

        with with_user(_user(UserRole.SUPERADMIN)):
            assert isinstance(await processor.run(_SearchAction()), _Result)

    async def test_everyone_else_is_refused_without_a_permission_read(self) -> None:
        repository = _repository(Permission.full())
        processor = _processor(repository, _config_provider(enforcement_enabled=False))

        with with_user(_user()):
            with pytest.raises(InsufficientPrivilege):
                await processor.run(_SearchAction())

        repository.governed_permissions.assert_not_awaited()
