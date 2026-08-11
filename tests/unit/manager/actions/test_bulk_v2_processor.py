"""``actions/v2/bulk``'s processor carries what happened to each entity.

Splitting a bulk run into one audit row per entity is pointless if every row shares
one status, so the meta the monitors see must come from the result, not from the
action's input.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.bulk.result import (
    BaseBulkActionResult,
    BulkActionProcessResult,
    BulkEntityResult,
)
from ai.backend.manager.actions.v2.bulk.validator.base import BulkActionValidator


def _eid(raw: str) -> EntityID:
    return uuid.uuid5(uuid.NAMESPACE_OID, raw)


@dataclass
class _Action(BaseBulkAction):
    ids: list[EntityID]

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return self.ids

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
    def action_name(cls) -> str:
        return "delete_sessions"


@dataclass
class _Result(BaseBulkActionResult):
    results: list[BulkEntityResult]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        return self.results


class _RecordingMonitor(BulkActionMonitor):
    def __init__(self) -> None:
        self.done_results: list[BulkActionProcessResult] = []

    @override
    async def prepare(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseBulkAction, result: BulkActionProcessResult) -> None:
        self.done_results.append(result)


class _DenyingValidator(BulkActionValidator):
    @override
    async def validate(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        raise PermissionDeniedError("nope")


def _ok(entity_id: EntityID) -> BulkEntityResult:
    return BulkEntityResult(
        entity_id=entity_id,
        status=OperationStatus.SUCCESS,
        description="Success",
        error_code=None,
    )


@pytest.fixture
def action() -> _Action:
    return _Action(ids=[_eid("a"), _eid("b"), _eid("c")])


async def test_partial_failure_keeps_each_entity_status(action: _Action) -> None:
    results = [
        _ok(_eid("a")),
        BulkEntityResult(
            entity_id=_eid("b"),
            status=OperationStatus.ERROR,
            description="still mounted",
            error_code=None,
        ),
        _ok(_eid("c")),
    ]

    async def run(_: _Action) -> _Result:
        return _Result(results=results)

    monitor = _RecordingMonitor()
    await BulkActionProcessor[_Action, _Result](func=run, monitors=[monitor]).run(action)

    meta = monitor.done_results[0].meta
    assert [(r.entity_id, r.status) for r in meta.entity_results] == [
        (_eid("a"), OperationStatus.SUCCESS),
        (_eid("b"), OperationStatus.ERROR),
        (_eid("c"), OperationStatus.SUCCESS),
    ]


async def test_all_entities_succeeding_summarizes_as_success(action: _Action) -> None:
    async def run(a: _Action) -> _Result:
        return _Result(results=[_ok(entity_id) for entity_id in a.entity_ids()])

    monitor = _RecordingMonitor()
    await BulkActionProcessor[_Action, _Result](func=run, monitors=[monitor]).run(action)

    assert all(
        r.status is OperationStatus.SUCCESS for r in monitor.done_results[0].meta.entity_results
    )


async def test_denial_is_attributed_to_every_named_entity(action: _Action) -> None:
    async def run(_: _Action) -> _Result:
        raise AssertionError("must not run")

    monitor = _RecordingMonitor()
    processor = BulkActionProcessor[_Action, _Result](
        func=run, monitors=[monitor], validators=[_DenyingValidator()]
    )

    with pytest.raises(PermissionDeniedError):
        await processor.run(action)

    meta = monitor.done_results[0].meta
    assert [r.entity_id for r in meta.entity_results] == list(action.entity_ids())
    assert all(r.status is OperationStatus.DENIED for r in meta.entity_results)
