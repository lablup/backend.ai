"""A gated bulk lookup answers per key, and a miss and a denial answer the same."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import PartialBulkActionValidator
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.lookup.bulk_base import BaseBulkLookupAction, BulkLookupKeyResult
from ai.backend.manager.actions.v2.lookup.bulk_monitor.base import BulkLookupActionMonitor
from ai.backend.manager.actions.v2.lookup.bulk_result import BulkLookupActionProcessResult
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.actions.v2.lookup.partial_bulk_processor import (
    PartialBulkLookupActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import BulkLookupOpsResult
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission

_READABLE = "readable@example.com"
_UNREADABLE = "unreadable@example.com"
_MISSING = "missing@example.com"
_READABLE_ID = UserID(uuid.uuid4())
_UNREADABLE_ID = UserID(uuid.uuid4())


@dataclass(frozen=True)
class _EmailKey(LookupKey):
    email: str

    @override
    def kind(self) -> str:
        return "email"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"email": self.email}


@dataclass
class _Action(BaseBulkLookupAction):
    emails: Sequence[str]

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @classmethod
    @override
    def action_name(cls) -> str:
        return "bulk_lookup_users"

    @override
    def lookup_keys(self) -> Sequence[LookupKey]:
        return [_EmailKey(email) for email in self.emails]


class _DenyingValidator(PartialBulkActionValidator):
    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        return {
            entity_id: NotEnoughPermission("no read")
            for entity_id in meta.entity_ids
            if entity_id == _UNREADABLE_ID
        }


class _SuperadminValidator(PartialBulkActionValidator):
    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        return {}


class _RecordingMonitor(BulkLookupActionMonitor):
    done_results: list[BulkLookupActionProcessResult]

    def __init__(self) -> None:
        self.done_results = []

    @override
    async def prepare(self, meta: BulkLookupActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: BulkLookupActionTriggerMeta, result: BulkLookupActionProcessResult
    ) -> None:
        self.done_results.append(result)


async def _lookup(action: _Action) -> BulkLookupOpsResult[str, UserID]:
    known = {_READABLE: _READABLE_ID, _UNREADABLE: _UNREADABLE_ID}
    resolved = {email: known[email] for email in action.emails if email in known}
    return BulkLookupOpsResult(
        resolved=resolved,
        failures={
            email: EntityNotFoundError(
                "No entity matches the given key",
                entity_type=UserEntityType(),
                operation=ActionOperationType.LOOKUP,
            )
            for email in action.emails
            if email not in known
        },
        key_results=[
            BulkLookupKeyResult(
                key=_EmailKey(email),
                status=OperationStatus.SUCCESS if email in known else OperationStatus.ERROR,
                description="",
                error_code=None,
                entity_id=known.get(email),
            )
            for email in action.emails
        ],
    )


def _user(role: UserRole) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=role is UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def action() -> _Action:
    return _Action(emails=[_READABLE, _UNREADABLE, _MISSING])


class TestPartialBulkLookupActionProcessor:
    async def test_a_reachable_key_resolves_and_the_rest_fail_alike(self, action: _Action) -> None:
        processor = PartialBulkLookupActionProcessor[_Action](
            _lookup, partial_validators=[_DenyingValidator()]
        )

        with with_user_context(_user(UserRole.USER)):
            result = await processor.run(action)

        assert result.resolved == {_READABLE: _READABLE_ID}
        assert set(result.failures) == {_UNREADABLE, _MISSING}
        assert all(isinstance(error, GenericBadRequest) for error in result.failures.values())

    async def test_a_superadmin_gets_the_miss_as_is(self, action: _Action) -> None:
        processor = PartialBulkLookupActionProcessor[_Action](
            _lookup, partial_validators=[_SuperadminValidator()]
        )

        with with_user_context(_user(UserRole.SUPERADMIN)):
            result = await processor.run(action)

        assert result.resolved == {_READABLE: _READABLE_ID, _UNREADABLE: _UNREADABLE_ID}
        assert isinstance(result.failures[_MISSING], EntityNotFoundError)

    async def test_the_record_keeps_the_denial_apart_from_the_miss(self, action: _Action) -> None:
        monitor = _RecordingMonitor()
        processor = PartialBulkLookupActionProcessor[_Action](
            _lookup, partial_validators=[_DenyingValidator()], monitors=[monitor]
        )

        with with_user_context(_user(UserRole.USER)):
            await processor.run(action)

        statuses = [one.status for one in monitor.done_results[0].meta.key_results]
        assert statuses == [OperationStatus.SUCCESS, OperationStatus.DENIED, OperationStatus.ERROR]
