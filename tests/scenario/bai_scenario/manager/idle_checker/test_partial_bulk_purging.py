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
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
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
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 검사기 {len(laid.laid)}개{besides}를 한 번에 purge 함"

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
        return (
            "슈퍼관리자가 검사기 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지운 검사기로 오고 "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
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
        return (
            "아무 권한도 받지 않은 사용자가 검사기 여럿을 한 번에 purge 하려 하면, 지운 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
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


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesSeveral(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
