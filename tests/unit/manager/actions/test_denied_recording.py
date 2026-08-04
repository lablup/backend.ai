"""A rejected action must reach the monitors, tagged DENIED.

Monitors used to wrap only execution, which the processor reached after validation
had passed, so a permission denial left no trace at all.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.validator.base import (
    SingleEntityActionValidator,
)
from ai.backend.manager.errors.common import InternalServerError

_ENTITY_ID: EntityID = uuid.uuid4()


@dataclass
class _Action(BaseSingleEntityAction):
    @override
    def entity_id(self) -> EntityID:
        return _ENTITY_ID

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("session")

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @classmethod
    @override
    def required_permission(cls) -> Permission:
        return Permission.SOFT_DELETE


@dataclass
class _Result:
    pass


class _RecordingMonitor(SingleEntityActionMonitor):
    def __init__(self) -> None:
        self.prepared = 0
        self.done_results: list[SingleEntityActionProcessResult] = []

    @override
    async def prepare(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        self.prepared += 1

    @override
    async def done(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        self.done_results.append(result)


class _DenyingValidator(SingleEntityActionValidator):
    @override
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        raise PermissionDeniedError("nope")


class _BrokenValidator(SingleEntityActionValidator):
    @override
    async def validate(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        raise InternalServerError("the permission lookup itself blew up")


async def _run(action: _Action) -> _Result:
    return _Result()


async def test_denied_validation_reaches_monitors_as_denied() -> None:
    monitor = _RecordingMonitor()
    processor = SingleEntityActionProcessor[_Action, _Result](
        func=_run, monitors=[monitor], validators=[_DenyingValidator()]
    )

    with pytest.raises(PermissionDeniedError):
        await processor.run(_Action())

    assert monitor.prepared == 1
    meta = monitor.done_results[0].meta
    assert meta.status is OperationStatus.DENIED
    assert meta.entity_id == _ENTITY_ID


async def test_non_authorization_validation_failure_is_an_error_not_a_denial() -> None:
    monitor = _RecordingMonitor()
    processor = SingleEntityActionProcessor[_Action, _Result](
        func=_run, monitors=[monitor], validators=[_BrokenValidator()]
    )

    with pytest.raises(InternalServerError):
        await processor.run(_Action())

    assert monitor.done_results[0].meta.status is OperationStatus.ERROR


async def test_successful_run_is_still_reported_as_success() -> None:
    monitor = _RecordingMonitor()
    processor = SingleEntityActionProcessor[_Action, _Result](func=_run, monitors=[monitor])

    await processor.run(_Action())

    assert monitor.done_results[0].meta.status is OperationStatus.SUCCESS
