"""``actions/v2/membership``: one entity moves into scopes or out of them, and the
entity and every scope have to permit it."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.membership.base import BaseMembershipAction
from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.processor import MembershipActionProcessor
from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.actions.v2.membership.validator.base import MembershipActionValidator
from ai.backend.manager.actions.v2.membership.validator.rbac import (
    VirtualEntityMembershipActionRBACValidator,
)
from ai.backend.manager.errors.permission import NotEnoughPermission

_REGISTRY_ID = ContainerRegistryID(uuid.uuid5(uuid.NAMESPACE_OID, "registry"))
_PUBLIC_ID = GlobalEntityID(uuid.uuid5(uuid.NAMESPACE_OID, "public"))


@dataclass
class _MoveAction(BaseMembershipAction):
    @override
    def entity(self) -> EntityIdentifier:
        return _REGISTRY_ID

    @override
    def scopes(self) -> Sequence[EntityIdentifier]:
        return (_PUBLIC_ID,)

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "move_registry_into_public"


class _RecordingMonitor(MembershipActionMonitor):
    def __init__(self) -> None:
        self.done_calls: list[
            tuple[MembershipActionTriggerMeta, MembershipActionProcessResult]
        ] = []

    @override
    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        self.done_calls.append((meta, result))


class _DenyingValidator(MembershipActionValidator):
    @override
    async def validate(self, meta: MembershipActionTriggerMeta) -> None:
        raise PermissionDeniedError("denied")


class TestMembershipActionProcessor:
    async def test_the_run_names_the_entity_and_the_scopes(self) -> None:
        monitor = _RecordingMonitor()

        async def run(_: _MoveAction) -> str:
            return "moved"

        processor = MembershipActionProcessor[_MoveAction, str](run, monitors=[monitor])
        assert await processor.run(_MoveAction()) == "moved"

        (meta, result) = monitor.done_calls[0]
        assert meta.entity == _REGISTRY_ID
        assert list(meta.scopes) == [_PUBLIC_ID]
        assert result.meta.status is OperationStatus.SUCCESS

    async def test_a_denial_stops_the_run_and_is_recorded(self) -> None:
        monitor = _RecordingMonitor()
        ran = False

        async def run(_: _MoveAction) -> None:
            nonlocal ran
            ran = True

        processor = MembershipActionProcessor[_MoveAction, None](
            run, monitors=[monitor], validators=[_DenyingValidator()]
        )
        with pytest.raises(PermissionDeniedError):
            await processor.run(_MoveAction())

        assert not ran
        (_, result) = monitor.done_calls[0]
        assert result.meta.status is OperationStatus.DENIED


class TestEntityAndEveryScopeMustPermit:
    def _validator(
        self, held: dict[uuid.UUID, Permission]
    ) -> VirtualEntityMembershipActionRBACValidator:
        repository = MagicMock()

        async def owned(keys: list[Any]) -> dict[Any, Permission]:
            return {key: held.get(key.entity, Permission.NONE) for key in keys}

        repository.owned_permissions = owned
        config_provider = MagicMock()
        config_provider.config.manager.rbac.enforcement_enabled = True
        return VirtualEntityMembershipActionRBACValidator(repository, config_provider)

    def _meta(self) -> MembershipActionTriggerMeta:
        action = _MoveAction()
        return MembershipActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=MagicMock(),
            entity=action.entity(),
            scopes=action.scopes(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

    def _user(self, *, superadmin: bool = False) -> UserData:
        return UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=superadmin,
            is_superadmin=superadmin,
            role=UserRole.SUPERADMIN if superadmin else UserRole.USER,
            domain_name="default",
            domain_id=MagicMock(),
        )

    async def test_update_on_both_passes(self) -> None:
        validator = self._validator({
            _REGISTRY_ID: Permission.UPDATE,
            _PUBLIC_ID: Permission.UPDATE,
        })
        with with_user(self._user()):
            await validator.validate(self._meta())

    async def test_update_on_the_entity_alone_is_not_enough(self) -> None:
        validator = self._validator({_REGISTRY_ID: Permission.UPDATE})
        with with_user(self._user()):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(self._meta())

    async def test_update_on_the_scope_alone_is_not_enough(self) -> None:
        validator = self._validator({_PUBLIC_ID: Permission.UPDATE})
        with with_user(self._user()):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(self._meta())

    async def test_read_on_both_is_not_enough(self) -> None:
        validator = self._validator({_REGISTRY_ID: Permission.READ, _PUBLIC_ID: Permission.READ})
        with with_user(self._user()):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(self._meta())

    async def test_a_superadmin_bypasses_the_check(self) -> None:
        validator = self._validator({})
        with with_user(self._user(superadmin=True)):
            await validator.validate(self._meta())
