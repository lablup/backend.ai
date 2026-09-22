"""규칙 조회 — 하나를 id로, 여럿을 한 번에. 어느 쪽이든 권한 검사를 거친다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.notification import NotificationRuleID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.notification.response import NotificationRuleNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.notification import (
    ARuleAndACaller,
    ARuleAndSomeone,
    EachItemIsRefused,
    LoadedRules,
    ManyRulesAndACaller,
    NothingComesBack,
    TheRuleNode,
    TheRulesInTheOrderAsked,
    TwoRulesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[SeedingSession, Any, NotificationAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else f"규칙 {laid.rule.name}"
        return f"{laid.caller.username}이 {target} 조회"

    @override
    async def call(
        self, adapter: NotificationAdapter, laid: ARuleAndACaller
    ) -> NotificationRuleNode:
        with ActingAs(laid.caller):
            payload = await adapter.get_rule(uuid4() if self.unknown else laid.rule.id)
        return payload.item


@dataclass(frozen=True)
class ReadingManyByIds(When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]):
    """미리 만들어 둔 규칙들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_rules_by_ids"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 미리 만들어 둔 {len(laid.laid)}개와 없는 id 하나를 한 번에 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> LoadedRules:
        ids: Sequence[NotificationRuleID] = [
            *(one.id for one in laid.laid),
            NotificationRuleID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_rules_by_ids(ids)


@dataclass(frozen=True)
class ReadingTheLaidByIds(When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]):
    """미리 만들어 둔 규칙들만 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_rules_by_ids"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 미리 만들어 둔 {len(laid.laid)}개를 한 번에 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> LoadedRules:
        with ActingAs(laid.caller):
            return await adapter.batch_load_rules_by_ids([one.id for one in laid.laid])


@dataclass(frozen=True)
class ReadingNoIds(When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]):
    """빈 id 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_rules_by_ids"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        return f"{laid.caller.username}이 빈 id 목록으로 조회"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> LoadedRules:
        with ActingAs(laid.caller):
            return await adapter.batch_load_rules_by_ids([])


@dataclass(frozen=True)
class TheSuperadminReadsARule(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-rule-by-id"

    @override
    def describe(self) -> str:
        return "규칙 하나가 있고 슈퍼관리자가 id로 조회하면, 그 규칙 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-rule"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone()

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-rule-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미리 만들어 둔 규칙 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id에 해당하는 항목은 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyRulesAndACaller, LoadedRules]:
        return TheRulesInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerItem(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-rules-is-refused-per-item"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 규칙 둘을 한 번에 조회하면, "
            "호출은 거부되지 않고 항목마다 권한 부족 거부가 담긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone()

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]:
        return ReadingTheLaidByIds()

    @override
    def then(self) -> Then[ManyRulesAndACaller, LoadedRules]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[SeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-rule-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 조회하면 하위 계층을 부르지 않고 빈 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone()

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]:
        return ReadingNoIds()

    @override
    def then(self) -> Then[ManyRulesAndACaller, LoadedRules]:
        return NothingComesBack()


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsARule(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheSuperadminReadingAnUnknownIdIsNotFound(),
    TheSuperadminLoadsLaidAndMissing(started=datetime.now(UTC)),
    AUserGrantedNothingIsRefusedPerItem(),
    ABatchLoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_rules(
    scenario: ReadingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
