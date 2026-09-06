"""A bulk read answers for every id it was given, denials included.

The point of the shape is that an id the caller may not read and an id matching no row
are two different answers, so the processor is held to keeping them apart — in what it
returns and in what the monitors record.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Self, override

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.partial_processor import (
    PartialBulkActionProcessor,
    PublicPartialBulkActionProcessor,
)
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    PartialBulkEntityResult,
    PartialBulkResult,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import PartialBulkActionValidator
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.errors.user import UserNotFound

_STORAGE_ENTITY_TYPE = EntityType("object_storage")


class _StorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return _STORAGE_ENTITY_TYPE


def _eid(raw: str) -> _StorageID:
    return _StorageID(uuid.uuid5(uuid.NAMESPACE_OID, raw))


@dataclass
class _Action(BasePartialBulkAction):
    ids: list[_StorageID]

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return self.ids

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @classmethod
    @override
    def action_name(cls) -> str:
        return "bulk_get_object_storages"


@dataclass
class _WriteAction(_Action):
    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class _RecordingMonitor(BulkActionMonitor):
    def __init__(self) -> None:
        self.done_results: list[BulkActionProcessResult] = []

    @override
    async def prepare(self, meta: BulkActionTriggerMeta) -> None:
        return

    @override
    async def done(self, meta: BulkActionTriggerMeta, result: BulkActionProcessResult) -> None:
        self.done_results.append(result)


@dataclass
class _DenyingValidator(PartialBulkActionValidator):
    """Denies the ids it was built with, leaving the rest to the operation."""

    denied: list[_StorageID] = field(default_factory=list)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        return {entity_id: NotEnoughPermission("nope") for entity_id in self.denied}


class _Reader:
    """Stands in for the ops read: it knows one row, and reads the narrowed action."""

    def __init__(self, present: Sequence[_StorageID]) -> None:
        self._present = set(present)
        self.asked_for: list[EntityIdentifier] = []

    async def run(self, action: _Action) -> PartialBulkResult[str]:
        entity_ids = action.entity_ids()
        self.asked_for = list(entity_ids)
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[str].succeeded(entity_id, f"data:{entity_id}")
                if entity_id in self._present
                else PartialBulkEntityResult[str].failed(entity_id, EntityNotFoundError("gone"))
                for entity_id in entity_ids
            ]
        )


def _user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def action() -> _Action:
    return _Action(ids=[_eid("readable"), _eid("denied"), _eid("gone")])


async def test_a_denied_id_is_never_read(action: _Action) -> None:
    reader = _Reader(present=[_eid("readable"), _eid("denied")])
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        partial_validators=[_DenyingValidator(denied=[_eid("denied")])],
    )

    await processor.run(action)

    assert reader.asked_for == [_eid("readable"), _eid("gone")]


async def test_a_denial_and_a_miss_carry_different_errors(action: _Action) -> None:
    reader = _Reader(present=[_eid("readable"), _eid("denied")])
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        partial_validators=[_DenyingValidator(denied=[_eid("denied")])],
    )

    result = await processor.run(action)

    assert result.values() == {_eid("readable"): f"data:{_eid('readable')}"}
    errors = result.errors()
    assert isinstance(errors[_eid("denied")], NotEnoughPermission)
    assert isinstance(errors[_eid("gone")], EntityNotFoundError)


async def test_every_named_entity_is_recorded_with_its_own_status(action: _Action) -> None:
    reader = _Reader(present=[_eid("readable"), _eid("denied")])
    monitor = _RecordingMonitor()
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        monitors=[monitor],
        partial_validators=[_DenyingValidator(denied=[_eid("denied")])],
    )

    await processor.run(action)

    meta = monitor.done_results[0].meta
    assert {r.entity_id: r.status for r in meta.entity_results} == {
        _eid("readable"): OperationStatus.SUCCESS,
        _eid("gone"): OperationStatus.ERROR,
        _eid("denied"): OperationStatus.DENIED,
    }


async def test_nothing_is_read_when_every_id_is_denied(action: _Action) -> None:
    reader = _Reader(present=list(action.ids))
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        partial_validators=[_DenyingValidator(denied=list(action.ids))],
    )

    result = await processor.run(action)

    assert reader.asked_for == []
    assert result.values() == {}
    assert set(result.errors()) == set(action.ids)


async def test_the_public_path_denies_nothing(action: _Action) -> None:
    reader = _Reader(present=list(action.ids))
    processor = PublicPartialBulkActionProcessor[_Action, str](_Action, reader.run)

    with with_user(_user()):
        result = await processor.run(action)

    assert reader.asked_for == list(action.ids)
    assert set(result.values()) == set(action.ids)


async def test_the_public_path_still_needs_an_authenticated_caller(action: _Action) -> None:
    reader = _Reader(present=list(action.ids))
    processor = PublicPartialBulkActionProcessor[_Action, str](_Action, reader.run)

    with pytest.raises(UserNotFound):
        await processor.run(action)


def test_the_public_path_rejects_a_write() -> None:
    reader = _Reader(present=[])
    with pytest.raises(ServerMisconfiguredError):
        PublicPartialBulkActionProcessor[_WriteAction, str](_WriteAction, reader.run)


async def test_the_answer_keeps_the_order_the_caller_asked_in(action: _Action) -> None:
    """The denied id is put back where it was named, not appended after the rest."""
    reader = _Reader(present=[_eid("readable"), _eid("denied")])
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        partial_validators=[_DenyingValidator(denied=[_eid("denied")])],
    )

    result = await processor.run(action)

    assert [item.entity_id for item in result.items] == list(action.entity_ids())


async def test_a_denial_is_marked_apart_from_a_failure(action: _Action) -> None:
    reader = _Reader(present=[_eid("readable"), _eid("denied")])
    processor = PartialBulkActionProcessor[_Action, str](
        reader.run,
        partial_validators=[_DenyingValidator(denied=[_eid("denied")])],
    )

    result = await processor.run(action)

    assert {item.entity_id: item.is_denied for item in result.items} == {
        _eid("readable"): False,
        _eid("denied"): True,
        _eid("gone"): False,
    }
