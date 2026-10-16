"""도메인 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkUpdateDomainItemInput,
    PartialBulkUpdateDomainsInput,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import (
    DomainLook,
    ManyDomainsAndACaller,
    ManyDomainsAndSomeone,
    NothingIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[DomainNode]
type DomainStep = Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyDomainsAndACaller, DomainAdapter, Edited]):
    """대상 도메인들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return f"{laid.caller.username}이 도메인 {len(laid.elsewhere())}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateDomainsInput(
                    items=[
                        PartialBulkUpdateDomainItemInput(
                            id=domain.id, input=UpdateDomainInput(description=EDITED)
                        )
                        for domain in laid.elsewhere()
                    ]
                )
            )


@dataclass(frozen=True)
class EveryTargetIsEdited(Then[ManyDomainsAndACaller, Edited]):
    """대상이 모두 새 설명을 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "대상 도메인이 모두 새 설명으로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.elsewhere()
        look = DomainLook(self.started, described=EDITED)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(targets)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, domain) in enumerate(zip(payload.successes, targets, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, domain)
        return verdicts


@dataclass(frozen=True)
class TheSuperadminEditsSeveralDomains(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-domains-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return EveryTargetIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-domains"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 도메인 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


SCENARIOS: list[DomainStep] = [
    TheSuperadminEditsSeveralDomains(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
