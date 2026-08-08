"""The public path of the global layer: authentication only, and reads only.

``PublicActionProcessor`` runs ``BaseGlobalAction`` reads without the SUPERADMIN
gate, so two invariants are worth pinning: a write action cannot be wired onto it
at all, and the gated ``GlobalActionProcessor`` keeps its SUPERADMIN gate untouched.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import GenericForbidden, ServerMisconfiguredError
from ai.backend.manager.errors.user import UserNotFound


@dataclass
class _SearchAction(BaseGlobalAction):
    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("resource_slot_type")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @classmethod
    @override
    def action_name(cls) -> str:
        return "search_things"


@dataclass
class _GetAction(_SearchAction):
    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @classmethod
    @override
    def action_name(cls) -> str:
        return "get_thing"


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


class _RecordingMonitor(GlobalActionMonitor):
    def __init__(self) -> None:
        self.done_results: list[GlobalActionProcessResult] = []

    @override
    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        self.done_results.append(result)


def _user(*, is_authorized: bool = True, is_superadmin: bool = False) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=is_authorized,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=UserRole.SUPERADMIN if is_superadmin else UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


def test_only_get_and_search_actions_can_be_wired_public() -> None:
    PublicActionProcessor[_GetAction, _Result](_GetAction, _run)
    PublicActionProcessor[_SearchAction, _Result](_SearchAction, _run)

    with pytest.raises(ServerMisconfiguredError):
        PublicActionProcessor[_CreateAction, _Result](_CreateAction, _run)


async def test_the_public_path_rejects_a_missing_user_context() -> None:
    processor = PublicActionProcessor[_SearchAction, _Result](_SearchAction, _run)

    with pytest.raises(UserNotFound):
        await processor.run(_SearchAction())


async def test_the_public_path_rejects_an_unauthorized_user() -> None:
    processor = PublicActionProcessor[_SearchAction, _Result](_SearchAction, _run)

    with with_user(_user(is_authorized=False)):
        with pytest.raises(GenericForbidden):
            await processor.run(_SearchAction())


async def test_the_public_path_passes_a_regular_authenticated_user() -> None:
    processor = PublicActionProcessor[_SearchAction, _Result](_SearchAction, _run)

    with with_user(_user()):
        result = await processor.run(_SearchAction())

    assert isinstance(result, _Result)


async def test_a_public_denial_still_reaches_the_monitors() -> None:
    monitor = _RecordingMonitor()
    processor = PublicActionProcessor[_SearchAction, _Result](
        _SearchAction, _run, monitors=[monitor]
    )

    with with_user(_user(is_authorized=False)):
        with pytest.raises(GenericForbidden):
            await processor.run(_SearchAction())

    assert monitor.done_results[0].meta.status is OperationStatus.DENIED


async def test_the_global_path_still_gates_on_superadmin() -> None:
    processor = GlobalActionProcessor[_SearchAction, _Result](_run)

    with with_user(_user()):
        with pytest.raises(InsufficientPrivilege):
            await processor.run(_SearchAction())

    with with_user(_user(is_superadmin=True)):
        result = await processor.run(_SearchAction())

    assert isinstance(result, _Result)
