"""``actions/v2/relation``: a link is answered for by both ends and names no kind.

A relation row stands between two entities and is neither of them, so the action carries
no entity type. With no type there is no "permission on this type within this scope" to
ask, and the only thing left is the permission on each named scope itself — which is why
the shape is separate from the scope one rather than a variant of it.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.actions.v2.relation.monitor.base import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.actions.v2.relation.validator.base import RelationActionValidator
from ai.backend.manager.actions.v2.relation.validator.rbac import (
    VirtualEntityRelationActionRBACValidator,
)
from ai.backend.manager.errors.permission import NotEnoughPermission

_RESOURCE_GROUP = ScopeType(EntityType("resource_group"))
_DOMAIN = ScopeType(EntityType("domain"))

_RG_ID = uuid.uuid5(uuid.NAMESPACE_OID, "rg")
_DOMAIN_ID = uuid.uuid5(uuid.NAMESPACE_OID, "domain")


@dataclass
class _LinkAction(BaseRelationAction):
    scopes: list[ScopeRef]

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return self.scopes

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @classmethod
    @override
    def action_name(cls) -> str:
        return "link_resource_group_to_domain"


def _action(*scopes: ScopeRef) -> _LinkAction:
    return _LinkAction(scopes=list(scopes))


def _rg() -> ScopeRef:
    return ScopeRef(scope_type=_RESOURCE_GROUP, scope_id=_RG_ID)


def _domain() -> ScopeRef:
    return ScopeRef(scope_type=_DOMAIN, scope_id=_DOMAIN_ID)


class _RecordingMonitor(RelationActionMonitor):
    def __init__(self) -> None:
        self.done_calls: list[tuple[RelationActionTriggerMeta, RelationActionProcessResult]] = []

    @override
    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        self.done_calls.append((meta, result))


class _DenyingValidator(RelationActionValidator):
    @override
    async def validate(self, meta: RelationActionTriggerMeta) -> None:
        raise PermissionDeniedError("denied")


class TestRelationActionProcessor:
    async def test_the_run_names_both_ends(self) -> None:
        monitor = _RecordingMonitor()

        async def run(_: _LinkAction) -> str:
            return "linked"

        assert (
            await RelationActionProcessor[_LinkAction, str](run, monitors=[monitor]).run(
                _action(_rg(), _domain())
            )
            == "linked"
        )

        (meta, result) = monitor.done_calls[0]
        assert [(s.scope_type, s.scope_id) for s in meta.scope_targets] == [
            (_RESOURCE_GROUP, _RG_ID),
            (_DOMAIN, _DOMAIN_ID),
        ]
        assert result.meta.status is OperationStatus.SUCCESS

    async def test_the_action_carries_no_entity_type(self) -> None:
        # The absence is the point: with a type the check would read it at each scope,
        # and a relation has none to read.
        assert not hasattr(_LinkAction, "entity_type")

    async def test_a_denial_stops_the_run_and_is_recorded(self) -> None:
        monitor = _RecordingMonitor()
        ran = False

        async def run(_: _LinkAction) -> None:
            nonlocal ran
            ran = True

        processor = RelationActionProcessor[_LinkAction, None](
            run, monitors=[monitor], validators=[_DenyingValidator()]
        )
        with pytest.raises(PermissionDeniedError):
            await processor.run(_action(_rg(), _domain()))

        assert not ran
        (meta, result) = monitor.done_calls[0]
        assert result.meta.status is OperationStatus.DENIED
        assert len(meta.scope_targets) == 2

    async def test_a_monitor_failure_does_not_fail_the_run(self) -> None:
        class _BrokenMonitor(RelationActionMonitor):
            @override
            async def prepare(self, meta: RelationActionTriggerMeta) -> None:
                raise RuntimeError("monitor down")

            @override
            async def done(
                self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
            ) -> None:
                raise RuntimeError("monitor down")

        async def run(_: _LinkAction) -> str:
            return "linked"

        processor = RelationActionProcessor[_LinkAction, str](run, monitors=[_BrokenMonitor()])
        assert await processor.run(_action(_rg(), _domain())) == "linked"


class TestEveryEndMustPermitTheRun:
    def _validator(self, permitted: set[uuid.UUID]) -> VirtualEntityRelationActionRBACValidator:
        repository = MagicMock()

        async def check(keys: list[Any], permission: Any) -> dict[Any, bool]:
            return {key: key.entity in permitted for key in keys}

        repository.check_bulk_permission_via_virtual_entity = check
        config_provider = MagicMock()
        config_provider.config.manager.rbac.enforcement_enabled = True
        return VirtualEntityRelationActionRBACValidator(repository, config_provider)

    def _meta(self, action: _LinkAction) -> RelationActionTriggerMeta:
        return RelationActionTriggerMeta(
            action_id=uuid.uuid4(),
            started_at=MagicMock(),
            scope_targets=action.scope_targets(),
            operation_type=action.operation_type(),
            action_name=action.action_name(),
        )

    @pytest.fixture
    def user(self) -> UserData:
        return UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
            domain_id=MagicMock(),
        )

    async def test_both_ends_permitted_passes(self, user: UserData) -> None:
        validator = self._validator({_RG_ID, _DOMAIN_ID})
        with with_user(user):
            await validator.validate(self._meta(_action(_rg(), _domain())))

    async def test_one_end_alone_is_not_enough(self, user: UserData) -> None:
        # The hole a single-scope shape leaves: it would ask about the domain and never
        # about the resource group.
        validator = self._validator({_DOMAIN_ID})
        with with_user(user):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(self._meta(_action(_rg(), _domain())))

    async def test_the_other_end_alone_is_not_enough(self, user: UserData) -> None:
        validator = self._validator({_RG_ID})
        with with_user(user):
            with pytest.raises(NotEnoughPermission):
                await validator.validate(self._meta(_action(_rg(), _domain())))

    async def test_a_superadmin_bypasses_the_check(self) -> None:
        superadmin = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name="default",
            domain_id=MagicMock(),
        )
        validator = self._validator(set())
        with with_user(superadmin):
            await validator.validate(self._meta(_action(_rg(), _domain())))
