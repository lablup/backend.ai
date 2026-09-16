"""여러 id로 조회 — id마다 그 기록이 가리키는 엔티티의 읽기 권한을 검사하고, 항목마다 따로 응답한다.

볼 수 없는 기록은 그 항목만 거부되고 나머지는 반환된다. 없는 id는 누가 조회하든 빈 항목이다. 빈
목록은 권한 검사도 거치지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.audit_log import (
    Loaded,
    ProjectRecordsToLoad,
    RecordsToLoad,
    TheSlotsInOrder,
    TwoRecordsToRead,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type LoadingStep = Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]


@dataclass(frozen=True)
class LoadingWithAGap(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """있는 id 둘 사이에 없는 id 하나를 끼워 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 있는 id 둘과 없는 id 하나를 한 번에 조회"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                AuditLogID(laid.first[0]),
                AuditLogID(uuid4()),
                AuditLogID(laid.second[0]),
            ])


@dataclass(frozen=True)
class LoadingReadableUnreadableAndMissing(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """읽을 수 있는 기록, 읽을 수 없는 기록, 없는 id 순으로 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 읽을 수 있는 기록, 읽을 수 없는 기록, 없는 id 순으로 조회"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                AuditLogID(laid.first[0]),
                AuditLogID(laid.second[0]),
                AuditLogID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingNothing(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """빈 목록을 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로 조회"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class LoadingBoth(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """있는 id 둘을 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 있는 id 둘을 한 번에 조회"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                AuditLogID(laid.first[0]),
                AuditLogID(laid.second[0]),
            ])


@dataclass(frozen=True)
class AGrantedReaderIsAnsweredPerSlot(
    Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-granted-reader-gets-a-node-a-refusal-and-a-gap-in-order"

    @override
    def describe(self) -> str:
        return (
            "한쪽 프로젝트에만 읽기 권한을 받은 사용자가 읽을 수 있는 기록, 읽을 수 없는 기록, "
            "없는 id를 한 번에 조회하면, 요청한 순서대로 기록 전체, 권한 부족, 빈 항목이 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return ProjectRecordsToLoad()

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheSlotsInOrder(("first", "refused", "gap"))


@dataclass(frozen=True)
class TheNodesComeBackWithAGap(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-present-and-absent-ids-is-answered-in-order-with-a-gap"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 있는 id 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingWithAGap()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheSlotsInOrder(("first", "gap", "second"))


@dataclass(frozen=True)
class AnEmptyListReadsNothing(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "reading-an-empty-list-answers-empty-without-passing-the-gate"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 조회하면, 권한 검사도 거치지 않고 빈 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.USER)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingNothing()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheSlotsInOrder(())


@dataclass(frozen=True)
class TheMonitorRoleWithoutAGrantIsRefusedPerSlot(
    Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-without-a-grant-is-refused-in-every-slot"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 모니터 역할 사용자가 id 둘을 조회하면, 항목마다 권한 부족으로 응답한다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.MONITOR)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingBoth()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheSlotsInOrder(("refused", "refused"))


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerSlot(
    Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-is-refused-in-every-slot-even-for-records-about-themselves"

    @override
    def describe(self) -> str:
        return "읽기 권한이 없는 사용자가 자기에 대한 기록 둘을 id로 조회하면, 항목마다 권한 부족으로 응답한다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.USER)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingBoth()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheSlotsInOrder(("refused", "refused"))


SCENARIOS: list[LoadingStep] = [
    AGrantedReaderIsAnsweredPerSlot(),
    TheNodesComeBackWithAGap(),
    AnEmptyListReadsNothing(),
    TheMonitorRoleWithoutAGrantIsRefusedPerSlot(),
    AUserGrantedNothingIsRefusedPerSlot(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
