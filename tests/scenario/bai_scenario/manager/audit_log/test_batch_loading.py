"""여러 id로 읽기 — id마다 답하는 모양이지만 전역 검색을 부른다.

그래서 권한이 없으면 id별로 갈리지 않고 요청 전체가 막힌다. 빈 목록은 문도 지나지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.audit_log import (
    OP_EARLY,
    OP_LATE,
    RecordsToLoad,
    TheNodesInOrder,
    TwoRecordsToRead,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.audit_log.response import AuditLogNode
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Loaded = list[AuditLogNode | None]
type LoadingStep = Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]


@dataclass(frozen=True)
class LoadingWithAGap(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """있는 id 둘 사이에 없는 id 하나를 끼워 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 있는 id 둘과 없는 id 하나를 한 번에"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                AuditLogID(laid.first[0]),
                AuditLogID(uuid4()),
                AuditLogID(laid.second[0]),
            ])


@dataclass(frozen=True)
class LoadingNothing(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """빈 목록을 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class LoadingBoth(When[RecordsToLoad, AuditLogAdapter, Loaded]):
    """있는 id 둘을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: RecordsToLoad) -> str:
        return f"{laid.caller.username}이 있는 id 둘을 한 번에"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsToLoad) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                AuditLogID(laid.first[0]),
                AuditLogID(laid.second[0]),
            ])


@dataclass(frozen=True)
class TheNodesComeBackWithAGap(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "reading-present-and-absent-ids-answers-each-in-order-with-a-gap"

    @override
    def describe(self) -> str:
        return "있는 id 둘과 없는 id 하나를 한 번에 읽으면, 준 순서대로 오고 없는 자리는 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingWithAGap()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheNodesInOrder((OP_LATE, None, OP_EARLY))


@dataclass(frozen=True)
class AnEmptyListReadsNothing(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "reading-an-empty-list-answers-empty-without-passing-the-gate"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 읽으면, 문도 지나지 않고 빈 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingNothing()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheNodesInOrder(())


@dataclass(frozen=True)
class TheMonitorRoleReadsById(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "the-monitor-role-reading-by-id-sees-the-same-nodes-as-the-superadmin"

    @override
    def describe(self) -> str:
        return (
            "이 읽기도 읽기이므로 모니터 역할 사용자가 id 둘을 읽으면, 슈퍼관리자와 같은 답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.MONITOR)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingBoth()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheNodesInOrder((OP_LATE, OP_EARLY))


@dataclass(frozen=True)
class APlainUserMayNotReadById(Scenario[SeedingSession, RecordsToLoad, AuditLogAdapter, Loaded]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-by-id"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자도 모니터도 아닌 사용자가 id 둘을 읽으면, 요청 전체가 역할 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RecordsToLoad]:
        return TwoRecordsToRead(role=UserRole.USER)

    @override
    def when(self) -> When[RecordsToLoad, AuditLogAdapter, Loaded]:
        return LoadingBoth()

    @override
    def then(self) -> Then[RecordsToLoad, Loaded]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[LoadingStep] = [
    TheNodesComeBackWithAGap(),
    AnEmptyListReadsNothing(),
    TheMonitorRoleReadsById(),
    APlainUserMayNotReadById(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
