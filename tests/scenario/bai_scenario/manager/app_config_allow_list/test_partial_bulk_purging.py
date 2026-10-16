"""allow_list 여럿 영구 삭제하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    PartialBulkPurgeAppConfigAllowListsInput,
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
from bai_scenario.components.domain import Mentions
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=1)

type Purged = PartialBulkPayload[AppConfigAllowListNode]
type PurgingStep = Scenario[
    TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged
]


@dataclass(frozen=True)
class PurgingBoth(When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]):
    """준비한 allow_list 둘을 한 번에 영구 삭제한다. `missing`이면 없는 ID도 함께 넣는다."""

    missing: bool = False

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: TwoEntriesAndACaller) -> str:
        besides = "와 존재하지 않는 ID" if self.missing else ""
        return f"{laid.caller.username}이 allow_list 둘{besides}를 한 번에 영구 삭제"

    @override
    async def call(self, adapter: AppConfigAllowListAdapter, laid: TwoEntriesAndACaller) -> Purged:
        ids = [laid.first.id, laid.second.id, *((MISSING,) if self.missing else ())]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeAppConfigAllowListsInput(ids=ids)
            )


@dataclass(frozen=True)
class BothArePurgedTheMissingFails(Then[TwoEntriesAndACaller, Purged]):
    """둘은 처리된 목록에, 없는 ID는 대상이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "allow_list 둘은 처리된 목록에, 없는 ID는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]]([laid.first.id, laid.second.id], "준비한 ID 둘"),
            ),
            Same("failed count", len(payload.failed), 1),
        ]
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(MISSING, "요청에 넣은 없는 ID")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NeitherIsPurged(Then[TwoEntriesAndACaller, Purged]):
    """처리된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "처리된 allow_list 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다"

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
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
class TheSuperadminPurgesBothAndIsToldOfTheMissing(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 allow_list 둘과 존재하지 않는 ID를 한 번에 영구 삭제하면, 둘은 처리된 "
            "목록에 오고 없는 ID는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]:
        return PurgingBoth(missing=True)

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Purged]:
        return BothArePurgedTheMissingFails()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-entries"

    @override
    def describe(self) -> str:
        return (
            "권한이 없는 일반 사용자가 allow_list 둘을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 "
            "둘 다 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone()

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]:
        return PurgingBoth()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Purged]:
        return NeitherIsPurged()


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesBothAndIsToldOfTheMissing(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
