"""A lookup records only what it failed to find.

Its key is all that identifies the run, so it goes to ``lookup_kind`` / ``lookup_key``
rather than being squeezed into ``entity_id``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.errors.user import UserNotFound

_RESOLVED: EntityID = uuid.uuid4()


@dataclass(frozen=True)
class _CanonicalKey(LookupKey):
    canonical: str
    architecture: str

    @override
    def kind(self) -> str:
        return "canonical+architecture"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"canonical": self.canonical, "architecture": self.architecture}


@dataclass
class _Action(BaseLookupAction):
    key: _CanonicalKey

    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return EntityType("image")

    @classmethod
    @override
    def action_name(cls) -> str:
        return "lookup_image"

    @override
    def lookup_key(self) -> LookupKey:
        return self.key


@dataclass
class _Result(BaseLookupActionResult):
    @override
    def resolved_entity_id(self) -> EntityID:
        return _RESOLVED


class _RecordingMonitor(LookupActionMonitor):
    def __init__(self) -> None:
        self.done_results: list[LookupActionProcessResult] = []

    @override
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        self.done_results.append(result)


@pytest.fixture
def authenticated_user() -> UserData:
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
    return _Action(key=_CanonicalKey(canonical="lablup/python:3.13", architecture="aarch64"))


def test_a_lookup_is_a_read_so_the_audit_read_rules_apply() -> None:
    assert _Action.operation_type() is ActionOperationType.LOOKUP
    assert _Action.operation_type() in ActionOperationType.read_operations()


def test_the_key_reports_its_shape_without_its_value(action: _Action) -> None:
    key = action.lookup_key()

    assert key.kind() == "canonical+architecture"
    assert "lablup/python:3.13" not in key.kind()
    assert key.to_dict() == {
        "canonical": "lablup/python:3.13",
        "architecture": "aarch64",
    }


async def test_a_failed_lookup_reaches_the_monitors(
    action: _Action, authenticated_user: UserData
) -> None:
    async def run(_: _Action) -> _Result:
        raise ImageNotFound("no such image")

    monitor = _RecordingMonitor()
    processor = LookupActionProcessor[_Action, _Result](func=run, monitors=[monitor])

    with with_user(authenticated_user):
        with pytest.raises(ImageNotFound):
            await processor.run(action)

    assert monitor.done_results[0].meta.status is OperationStatus.ERROR


async def test_a_resolved_lookup_returns_the_id(
    action: _Action, authenticated_user: UserData
) -> None:
    async def run(_: _Action) -> _Result:
        return _Result()

    monitor = _RecordingMonitor()
    processor = LookupActionProcessor[_Action, _Result](func=run, monitors=[monitor])

    with with_user(authenticated_user):
        result = await processor.run(action)

    assert result.resolved_entity_id() == _RESOLVED
    assert monitor.done_results[0].meta.status is OperationStatus.SUCCESS


async def test_an_unauthenticated_lookup_is_rejected(action: _Action) -> None:
    async def run(_: _Action) -> _Result:
        raise AssertionError("must not run")

    monitor = _RecordingMonitor()
    processor = LookupActionProcessor[_Action, _Result](func=run, monitors=[monitor])

    with pytest.raises(UserNotFound):
        await processor.run(action)

    assert monitor.done_results[0].meta.status is OperationStatus.ERROR
