from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.reconciler.types import BaseReconcilerCategory
from ai.backend.manager.metrics.reconciler import ReconcilerMetricObserver
from ai.backend.manager.sokovan.reconciler import (
    BaseReconcilerInfo,
    BaseReconcilerKind,
    BaseReconcilerResult,
    BaseReconcilerTargetStatuses,
    ReconcilerApplier,
    ReconcilerApplyInput,
    ReconcilerCoordinator,
    ReconcilerFlag,
    ReconcilerHandler,
    ReconcilerSource,
    ReconcilerStage,
    ReconcilerStageMetadata,
)
from ai.backend.manager.types import DistributedLockFactory


class FakeCategory(BaseReconcilerCategory):
    DEFAULT = "default"


class FakeKind(BaseReconcilerKind):
    DEFAULT = "fake-kind"


class FakeStatus(StrEnum):
    DEFAULT = "default"


@dataclass(frozen=True)
class FakeTargetStatuses(BaseReconcilerTargetStatuses):
    statuses: tuple[str, ...] = ()


@dataclass
class FakeInfo(BaseReconcilerInfo):
    ids: list[UUID] = field(default_factory=list)

    def entity_ids(self) -> Sequence[UUID]:
        return self.ids


@dataclass
class FakeResult(BaseReconcilerResult):
    processed: int = 0
    failed: int = 0

    def processed_count(self) -> int:
        return self.processed

    def failed_count(self) -> int:
        return self.failed


@dataclass
class CallLog:
    events: list[str] = field(default_factory=list)


class FakeSource(ReconcilerSource[FakeInfo, FakeCategory, FakeTargetStatuses]):
    def __init__(self, call_log: CallLog, info: FakeInfo) -> None:
        self._call_log = call_log
        self._info = info

    async def fetch_reconcile_info(
        self, category: FakeCategory, target_statuses: FakeTargetStatuses
    ) -> FakeInfo:
        self._call_log.events.append("fetch")
        return self._info


class FakeHandler(ReconcilerHandler[FakeInfo, FakeResult]):
    def __init__(self, call_log: CallLog, result: FakeResult) -> None:
        self._call_log = call_log
        self._result = result

    async def execute(self, reconcile_info: FakeInfo) -> FakeResult:
        self._call_log.events.append("execute")
        return self._result

    async def post_process(self, result: FakeResult) -> None:
        self._call_log.events.append("post_process")


class FakeApplier(
    ReconcilerApplier[FakeInfo, FakeResult, FakeCategory, FakeKind, FakeTargetStatuses, FakeStatus]
):
    def __init__(self, call_log: CallLog) -> None:
        self._call_log = call_log

    async def apply(
        self,
        apply_input: ReconcilerApplyInput[
            FakeInfo, FakeResult, FakeCategory, FakeKind, FakeTargetStatuses, FakeStatus
        ],
    ) -> None:
        self._call_log.events.append("apply")


class FakeFlag(ReconcilerFlag):
    def __init__(self, needed: bool) -> None:
        self._needed = needed

    async def check_mark_needed(self, reconcile_type: str) -> bool:
        return self._needed


def _make_metadata() -> ReconcilerStageMetadata[
    FakeCategory, FakeKind, FakeTargetStatuses, FakeStatus
]:
    return ReconcilerStageMetadata(
        category=FakeCategory.DEFAULT,
        kind=FakeKind.DEFAULT,
        target_statuses=FakeTargetStatuses(),
        name="fake",
        phase="fake",
        lock_id=None,
        transitions={},
    )


def _make_coordinator(
    call_log: CallLog,
    info: FakeInfo,
    needed: bool = True,
) -> ReconcilerCoordinator:
    stage: ReconcilerStage[
        FakeInfo, FakeResult, FakeCategory, FakeTargetStatuses, FakeKind, FakeStatus
    ] = ReconcilerStage(
        handler=FakeHandler(call_log, FakeResult(processed=len(info.entity_ids()))),
        source=FakeSource(call_log, info),
        applier=FakeApplier(call_log),
        metadata=_make_metadata(),
    )
    return ReconcilerCoordinator(
        stages={"fake": stage},
        lock_factory=cast(DistributedLockFactory, MagicMock()),
        config_provider=cast(ManagerConfigProvider, MagicMock(spec=ManagerConfigProvider)),
        flags=FakeFlag(needed=needed),
    )


async def test_process_runs_fetch_execute_apply_post_process_in_order() -> None:
    call_log = CallLog()
    coordinator = _make_coordinator(call_log, FakeInfo(ids=[uuid4()]))

    await coordinator.process("fake")

    assert call_log.events == ["fetch", "execute", "apply", "post_process"]


async def test_process_warns_on_unknown_type() -> None:
    call_log = CallLog()
    coordinator = _make_coordinator(call_log, FakeInfo(ids=[uuid4()]))

    await coordinator.process("unknown")

    assert call_log.events == []


async def test_process_if_needed_skips_when_flag_absent() -> None:
    call_log = CallLog()
    coordinator = _make_coordinator(call_log, FakeInfo(ids=[uuid4()]), needed=False)

    await coordinator.process_if_needed("fake")

    assert call_log.events == []


async def test_process_if_needed_runs_when_flag_present() -> None:
    call_log = CallLog()
    coordinator = _make_coordinator(call_log, FakeInfo(ids=[uuid4()]), needed=True)

    await coordinator.process_if_needed("fake")

    assert call_log.events == ["fetch", "execute", "apply", "post_process"]


def test_reconciler_metric_measure_succeeds() -> None:
    observer = ReconcilerMetricObserver.instance()
    with observer.measure("fake-kind", "fake", "execute"):
        pass
    observer.observe_processed("fake-kind", "fake", processed=3, failed=1)


def test_reconciler_metric_measure_reraises_on_failure() -> None:
    observer = ReconcilerMetricObserver.instance()
    with pytest.raises(ValueError):
        with observer.measure("fake-kind", "fake", "execute"):
            raise ValueError("boom")
