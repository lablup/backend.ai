"""The public paths of the global and partial bulk layers: authentication only, and reads only.

``PublicActionProcessor`` and ``PublicPartialBulkActionProcessor`` run reads with an
authentication check in place of the permission gate, and a write action cannot be wired
onto either. The permission gates are pinned in ``test_global_permission_gate`` and ``ops/``.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction
from ai.backend.manager.actions.v2.bulk.partial_processor import PublicPartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.processor import PublicActionProcessor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericForbidden, ServerMisconfiguredError
from ai.backend.manager.errors.user import UserNotFound


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
    async def prepare(self, action: BaseGlobalAction, meta: ActionTriggerMeta) -> None:
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

    with with_user_context(_user(is_authorized=False)):
        with pytest.raises(GenericForbidden):
            await processor.run(_SearchAction())


async def test_the_public_path_passes_a_regular_authenticated_user() -> None:
    processor = PublicActionProcessor[_SearchAction, _Result](_SearchAction, _run)

    with with_user_context(_user()):
        result = await processor.run(_SearchAction())

    assert isinstance(result, _Result)


async def test_a_public_denial_still_reaches_the_monitors() -> None:
    monitor = _RecordingMonitor()
    processor = PublicActionProcessor[_SearchAction, _Result](
        _SearchAction, _run, monitors=[monitor]
    )

    with with_user_context(_user(is_authorized=False)):
        with pytest.raises(GenericForbidden):
            await processor.run(_SearchAction())

    assert monitor.done_results[0].meta.status is OperationStatus.DENIED


_STORAGE_ENTITY_TYPE = ObjectStorageEntityType()


class _StorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return _STORAGE_ENTITY_TYPE


def _eid(raw: str) -> _StorageID:
    return _StorageID(uuid.uuid5(uuid.NAMESPACE_OID, raw))


@dataclass
class _BulkGetAction(BasePartialBulkAction):
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
class _BulkPurgeAction(_BulkGetAction):
    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


class _BulkReader:
    """Stands in for the ops read: it knows the rows it was given, and reads the narrowed action."""

    def __init__(self, present: Sequence[_StorageID]) -> None:
        self._present = set(present)
        self.asked_for: list[EntityIdentifier] = []

    async def run(self, action: _BulkGetAction) -> PartialBulkResult[str]:
        entity_ids = action.entity_ids()
        self.asked_for = list(entity_ids)
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[str].succeeded(entity_id, f"data:{entity_id}")
                if entity_id in self._present
                else PartialBulkEntityResult[str].failed(
                    entity_id, EntityNotFoundError(entity_type=_STORAGE_ENTITY_TYPE)
                )
                for entity_id in entity_ids
            ]
        )


def _bulk_action() -> _BulkGetAction:
    return _BulkGetAction(ids=[_eid("readable"), _eid("denied"), _eid("gone")])


async def test_the_public_bulk_path_denies_nothing() -> None:
    action = _bulk_action()
    reader = _BulkReader(present=list(action.ids))
    processor = PublicPartialBulkActionProcessor[_BulkGetAction, str](_BulkGetAction, reader.run)

    with with_user_context(_user()):
        result = await processor.run(action)

    assert reader.asked_for == list(action.ids)
    assert set(result.values()) == set(action.ids)


async def test_the_public_bulk_path_still_needs_an_authenticated_caller() -> None:
    action = _bulk_action()
    reader = _BulkReader(present=list(action.ids))
    processor = PublicPartialBulkActionProcessor[_BulkGetAction, str](_BulkGetAction, reader.run)

    with pytest.raises(UserNotFound):
        await processor.run(action)


def test_the_public_bulk_path_rejects_a_write() -> None:
    reader = _BulkReader(present=[])
    with pytest.raises(ServerMisconfiguredError):
        PublicPartialBulkActionProcessor[_BulkPurgeAction, str](_BulkPurgeAction, reader.run)
