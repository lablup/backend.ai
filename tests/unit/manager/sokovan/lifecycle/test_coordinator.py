from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.defs import LockID
from ai.backend.manager.metrics.lifecycle import LifecycleMetricObserver
from ai.backend.manager.sokovan.lifecycle import (
    LifecycleCoordinator,
    LifecycleEntitySource,
    LifecycleHandler,
    LifecycleNeededFlags,
    LifecycleResult,
    LifecycleStage,
    LifecycleTransitionApplier,
)
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class FakeEntity:
    entity_id: int

    def uuid(self) -> UUID:
        return UUID(int=self.entity_id)


@dataclass
class FakeResult(LifecycleResult):
    entities: Sequence[FakeEntity]

    def processed_count(self) -> int:
        return len(self.entities)

    def failed_count(self) -> int:
        return 0


@dataclass
class CallLog:
    events: list[str] = field(default_factory=list)


class FakeHandler(LifecycleHandler[FakeEntity, FakeResult, str, str, str]):
    def __init__(self, call_log: CallLog) -> None:
        self._call_log = call_log

    @classmethod
    def name(cls) -> str:
        return "fake"

    @classmethod
    def kind(cls) -> str:
        return "fake-kind"

    @classmethod
    def category(cls) -> str:
        return "fake-category"

    @property
    def lock_id(self) -> LockID | None:
        return None

    @classmethod
    def target_statuses(cls) -> str:
        return "fake-target"

    @classmethod
    def status_transitions(cls) -> str:
        return "fake-transitions"

    async def execute(self, entities: Sequence[FakeEntity]) -> FakeResult:
        self._call_log.events.append("execute")
        return FakeResult(entities=list(entities))

    async def post_process(self, result: FakeResult) -> None:
        self._call_log.events.append("post_process")


class FakeSource(LifecycleEntitySource[FakeEntity, FakeResult, str, str, str]):
    def __init__(self, call_log: CallLog, entities: list[FakeEntity]) -> None:
        self._call_log = call_log
        self._entities = entities

    async def fetch(
        self,
        handler: LifecycleHandler[FakeEntity, FakeResult, str, str, str],
    ) -> list[FakeEntity]:
        self._call_log.events.append("fetch")
        return list(self._entities)

    def extract_id(self, entity: FakeEntity) -> UUID:
        return entity.uuid()


class FakeApplier(LifecycleTransitionApplier[FakeEntity, FakeResult, str, str, str]):
    def __init__(self, call_log: CallLog) -> None:
        self._call_log = call_log

    async def apply(
        self,
        handler: LifecycleHandler[FakeEntity, FakeResult, str, str, str],
        result: FakeResult,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        self._call_log.events.append("apply")


class FakeFlags(LifecycleNeededFlags):
    def __init__(self, needed: bool) -> None:
        self._needed = needed
        self.marked: list[str] = []

    async def mark_needed(self, lifecycle_type: str) -> None:
        self.marked.append(lifecycle_type)

    async def load_and_delete(self, lifecycle_type: str) -> bool:
        return self._needed


def _make_coordinator(
    call_log: CallLog,
    entities: list[FakeEntity],
    needed: bool = True,
) -> tuple[LifecycleCoordinator, FakeFlags]:
    flags = FakeFlags(needed=needed)
    stage: LifecycleStage[FakeEntity, FakeResult, str, str, str] = LifecycleStage(
        handler=FakeHandler(call_log),
        source=FakeSource(call_log, entities),
        applier=FakeApplier(call_log),
    )
    coordinator = LifecycleCoordinator(
        stages={"fake": stage},
        flags=flags,
        lock_factory=cast(DistributedLockFactory, MagicMock()),
        config_provider=cast(ManagerConfigProvider, MagicMock(spec=ManagerConfigProvider)),
        task_specs=[],
    )
    return coordinator, flags


async def test_process_runs_fetch_execute_apply_post_process_in_order() -> None:
    call_log = CallLog()
    coordinator, _ = _make_coordinator(call_log, entities=[FakeEntity(1)])

    await coordinator.process("fake")

    assert call_log.events == ["fetch", "execute", "apply", "post_process"]


async def test_process_short_circuits_on_empty_fetch() -> None:
    call_log = CallLog()
    coordinator, _ = _make_coordinator(call_log, entities=[])

    await coordinator.process("fake")

    assert call_log.events == ["fetch"]


async def test_process_if_needed_skips_when_flag_absent() -> None:
    call_log = CallLog()
    coordinator, _ = _make_coordinator(call_log, entities=[FakeEntity(1)], needed=False)

    await coordinator.process_if_needed("fake")

    assert call_log.events == []


async def test_process_if_needed_runs_when_flag_present() -> None:
    call_log = CallLog()
    coordinator, _ = _make_coordinator(call_log, entities=[FakeEntity(1)], needed=True)

    await coordinator.process_if_needed("fake")

    assert call_log.events == ["fetch", "execute", "apply", "post_process"]


def test_lifecycle_metric_measure_succeeds() -> None:
    observer = LifecycleMetricObserver.instance()
    with observer.measure("fake-kind", "fake", "execute"):
        pass
    observer.observe_processed("fake-kind", "fake", processed=3, failed=1)


def test_lifecycle_metric_measure_reraises_on_failure() -> None:
    observer = LifecycleMetricObserver.instance()
    with pytest.raises(ValueError):
        with observer.measure("fake-kind", "fake", "execute"):
            raise ValueError("boom")
