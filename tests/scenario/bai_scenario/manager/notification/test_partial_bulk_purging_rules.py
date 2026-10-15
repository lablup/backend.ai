"""규칙 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.notification.request import (
    PartialBulkPurgeNotificationRulesInput,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationRuleNode
from ai.backend.manager.api.adapters.notification.adapter import NotificationAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.notification import (
    ManyRulesAndACaller,
    NothingIsProcessed,
    TheRulesComeBack,
    TwoRulesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[NotificationRuleNode]
type PurgingStep = Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryOne(When[ManyRulesAndACaller, NotificationAdapter, Purged]):
    """미리 만들어 둔 규칙을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_rules"

    @override
    def describe(self, laid: ManyRulesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 규칙 {len(laid.laid)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: NotificationAdapter, laid: ManyRulesAndACaller) -> Purged:
        ids: list[UUID] = [one.id for one in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge_rules(
                PartialBulkPurgeNotificationRulesInput(ids=ids)
            )


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-rules-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 규칙 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 모습으로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Purged]:
        return PurgingEveryOne(missing=self.missing)

    @override
    def then(self) -> Then[ManyRulesAndACaller, Purged]:
        return TheRulesComeBack(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyRulesAndACaller, NotificationAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-rules"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 규칙 여럿을 한 번에 purge 하려 하면, 지워진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRulesAndACaller]:
        return TwoRulesAndSomeone()

    @override
    def when(self) -> When[ManyRulesAndACaller, NotificationAdapter, Purged]:
        return PurgingEveryOne()

    @override
    def then(self) -> Then[ManyRulesAndACaller, Purged]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging_rules(
    scenario: PurgingStep, adapter: NotificationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
