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
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[TestSeedingSession, Any, NotificationAdapter, Any]


@dataclass(frozen=True)
class ReadingById(When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_rule"

    @override
    def describe(self, laid: ARuleAndACaller) -> str:
        if self.unknown:
            target_ko = "존재하지 않는 id"
            target_en = "an unknown id"
        else:
            target_ko = f"규칙 {laid.rule.name}"
            target_en = f"the rule {laid.rule.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko} 조회합니다",
            english=f"{laid.caller.username} gets {target_en}",
        )

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
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개와 없는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} rules created "
                "in advance and one unknown id"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch-loads the {len(laid.laid)} rules created in advance"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 빈 id 목록으로 조회합니다",
            english=f"{laid.caller.username} batch-loads with an empty id list",
        )

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> LoadedRules:
        with ActingAs(laid.caller):
            return await adapter.batch_load_rules_by_ids([])


@dataclass(frozen=True)
class TheSuperadminReadsARule(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-rule-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "규칙 하나가 있고 superadmin 이 id 로 조회하면, 그 규칙 전체가 응답으로 옵니다",
            english=("with one rule, when the superadmin gets it by id, the whole rule comes back"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheRuleNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 id 로 조회하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing gets a rule by id, "
                "it is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone()

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById()

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, ARuleAndACaller, NotificationAdapter, NotificationRuleNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin gets an id nothing answers to, "
                "it is rejected because no target is found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARuleAndACaller]:
        return ARuleAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARuleAndACaller, NotificationAdapter, NotificationRuleNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[ARuleAndACaller, NotificationRuleNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissing(
    Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-rule-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 규칙 둘과 없는 id 하나를 한 번에 조회하면, "
            "요청한 순서대로 반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch-loads two rules created in advance and one "
                "unknown id, they come back in the order asked and the item for the "
                "unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyRulesAndACaller, LoadedRules]:
        return TheRulesInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerItem(
    Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-rules-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 규칙 둘을 한 번에 조회하면, "
            "호출은 거부되지 않고 항목마다 권한 부족 거부가 담깁니다",
            english=(
                "when a user granted nothing batch-loads two rules, the call is not "
                "rejected and each item carries a rejection for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone()

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, LoadedRules]:
        return ReadingTheLaidByIds()

    @override
    def then(self) -> Then[ManyRulesAndACaller, LoadedRules]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, LoadedRules]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-rule-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "a batch load with an empty id list brings an empty response without "
                "calling the lower layer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRulesAndACaller]:
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
