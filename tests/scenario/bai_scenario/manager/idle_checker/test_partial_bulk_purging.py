"""유휴 검사기 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    PartialBulkPurgeIdleCheckersInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import IdleCheckerNode
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.idle_checker import (
    CheckersAndACaller,
    EveryCheckerIsPurged,
    NoCheckerIsPurged,
    SomeCheckersAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[IdleCheckerNode]
type PurgingStep = Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryChecker(When[CheckersAndACaller, IdleCheckerAdapter, Purged]):
    """심은 검사기들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_partial_bulk_purge"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        besides = (
            Says(" 와 없는 id 하나", english=" and a missing id")
            if self.missing is not None
            else ""
        )
        return Says(
            f"{laid.caller.username}이 유휴 검사기 {len(laid.laid)}개{besides}를 한 번에 "
            "purge 합니다",
            english=(
                f"{laid.caller.username} purges {len(laid.laid)} idle checkers"
                f"{in_language(besides, Language.ENGLISH)} in one call"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Purged:
        ids = [checker.id for checker in laid.laid]
        if self.missing is not None:
            ids.append(IdleCheckerID(self.missing))
        with ActingAs(laid.caller):
            return await adapter.admin_partial_bulk_purge(
                PartialBulkPurgeIdleCheckersInput(ids=ids)
            )


@dataclass(frozen=True)
class TheSuperadminPurgesSeveral(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-several-and-is-answered-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 유휴 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제한 유휴 "
            "검사기로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two idle checkers and a missing id in one call, the "
                "two come back as deleted idle checkers and the missing id comes back in the "
                "failed list because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Purged]:
        return PurgingEveryChecker(missing=self.missing)

    @override
    def then(self) -> Then[CheckersAndACaller, Purged]:
        return EveryCheckerIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-checkers"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 유휴 검사기 여럿을 한 번에 purge 하려 하면, 삭제한 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to purge several idle checkers in one call, "
                "none is deleted and all come back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Purged]:
        return PurgingEveryChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, Purged]:
        return NoCheckerIsPurged(reason="Insufficient permission")


@dataclass(frozen=True)
class PurgingCheckersAsNobody(When[CheckersAndACaller, IdleCheckerAdapter, Purged]):
    """사용자 컨텍스트 없이 한 번에 purge 한다."""

    @override
    def operation(self) -> str:
        return "admin_partial_bulk_purge"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 유휴 검사기 {len(laid.laid)}개를 한 번에 purge 합니다",
            english=f"purges {len(laid.laid)} idle checkers at once without a user context",
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Purged:
        return await adapter.admin_partial_bulk_purge(
            PartialBulkPurgeIdleCheckersInput(ids=[one.id for one in laid.laid])
        )


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-checker-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "검사기 둘이 있고 사용자 컨텍스트 없이 한 번에 purge 하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two checkers exist and are purged at once without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Purged]:
        return PurgingCheckersAsNobody()

    @override
    def then(self) -> Then[CheckersAndACaller, Purged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesSeveral(),
    AUserGrantedNothingPurgesNone(),
    APurgeCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
