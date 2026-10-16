"""allow_list 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    PartialBulkUpdateAppConfigAllowListsInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.app_config_allow_list import (
    TwoEntriesAndACaller,
    TwoEntriesAndSomeone,
)
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RANK = 150

type Edited = PartialBulkPayload[AppConfigAllowListNode]
type EditingStep = Scenario[
    TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited
]


@dataclass(frozen=True)
class ChangingBothRanks(When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited]):
    """준비한 allow_list 둘의 순위를 한 번에 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: TwoEntriesAndACaller) -> str:
        return f"{laid.caller.username}이 allow_list 둘의 순위를 한 번에 {RANK}(으)로 변경"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: TwoEntriesAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateAppConfigAllowListsInput(
                    items=[
                        UpdateAppConfigAllowListInput(id=entry.id, rank=RANK)
                        for entry in (laid.first, laid.second)
                    ]
                )
            )


@dataclass(frozen=True)
class BothAreReranked(Then[TwoEntriesAndACaller, Edited]):
    """둘 다 새 순위를 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "allow_list 둘이 모두 새 순위로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        targets = (laid.first, laid.second)
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(targets)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, entry) in enumerate(zip(payload.successes, targets, strict=False)):
            verdicts += [
                Held[UUID](f"successes[{i}].id", node.id, SameAs(entry.id, "준비한 ID")),
                Same(f"successes[{i}].config_name", node.config_name, entry.config_name),
                Same(f"successes[{i}].scope_type", node.scope_type, entry.scope_type),
                Same(f"successes[{i}].rank", node.rank, RANK),
                Held(f"successes[{i}].updated_at", node.updated_at, written),
            ]
        return verdicts


@dataclass(frozen=True)
class NeitherIsReranked(Then[TwoEntriesAndACaller, Edited]):
    """처리된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "처리된 allow_list 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = (laid.first, laid.second)
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(targets)),
        ]
        for i, (failure, entry) in enumerate(zip(payload.failed, targets, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(entry.id, "준비한 ID")),
                Held(f"failed[{i}].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class TheSuperadminReranksBoth(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reranks-several-entries-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 allow_list 둘의 순위를 한 번에 바꾸면, 둘 다 새 순위로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited]:
        return ChangingBothRanks()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Edited]:
        return BothAreReranked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReranksNone(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reranks-none-of-several-entries"

    @override
    def describe(self) -> str:
        return (
            "권한이 없는 일반 사용자가 allow_list 둘의 순위를 한 번에 바꾸려 하면, 바뀐 것 없이 "
            "둘 다 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone()

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Edited]:
        return ChangingBothRanks()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Edited]:
        return NeitherIsReranked()


SCENARIOS: list[EditingStep] = [
    TheSuperadminReranksBoth(started=datetime.now(UTC)),
    AUserGrantedNothingReranksNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
