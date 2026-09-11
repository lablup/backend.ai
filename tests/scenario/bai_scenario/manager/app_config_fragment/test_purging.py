"""조각 지우기 — 하나씩, 그리고 여럿을 한 번에.

지우기는 허용 항목을 보지 않는다. 조각은 허용 항목이 있는 동안만 존재하므로, 있는 조각은
언제나 자기 스코프에서 지울 수 있다. 여럿을 지우면 원소마다 답하고, 이 어댑터에는 soft
delete가 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    AFragmentAndACaller,
    AFragmentAndSomeone,
    SomeFragmentsAndACaller,
    SomeFragmentsAndSomeone,
    Whose,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    BulkPurgeAppConfigFragmentInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    BulkPurgeAppConfigFragmentPayload,
    PurgeAppConfigFragmentPayload,
)
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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
    Skipped,
    Then,
    Verdict,
    When,
)

type Purged = PurgeAppConfigFragmentPayload
type PurgingStep = Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
type BulkPurged = BulkPurgeAppConfigFragmentPayload
type BulkStep = Scenario[
    SeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged
]


@dataclass(frozen=True)
class Purging(When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]):
    """조각 하나를 지운다. id를 대지 않으면 심은 조각을 지운다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AFragmentAndACaller) -> str:
        called = (
            "아무것도 갖지 않은 id"
            if self.other is not None
            else f"{laid.fragment.config_name}의 조각"
        )
        return f"{laid.caller.username}이 {called}을 지움"

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: AFragmentAndACaller) -> Purged:
        wanted = AppConfigFragmentID(self.other) if self.other is not None else laid.fragment.id
        with ActingAs(laid.caller):
            return await adapter.purge(wanted)


@dataclass(frozen=True)
class PurgingMany(When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]):
    """자기 조각들, 남의 조각, 아무것도 갖지 않은 id를 한 번에 지운다."""

    @override
    def operation(self) -> str:
        return "bulk_purge"

    @override
    def describe(self, laid: SomeFragmentsAndACaller) -> str:
        return (
            f"{laid.caller.username}이 자기 조각 {len(laid.mine)}개, 다른 사용자의 조각, "
            "아무것도 갖지 않은 id를 한 번에 지움"
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: SomeFragmentsAndACaller
    ) -> BulkPurged:
        asked = [*(one.id for one in laid.mine), laid.theirs.id, AppConfigFragmentID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.bulk_purge(BulkPurgeAppConfigFragmentInput(ids=asked))


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[AFragmentAndACaller, Purged]):
    """지운 조각이 무엇인지 id로 답한다."""

    @override
    def says(self) -> str:
        return "지운 조각의 id를 답한다"

    @override
    def look(self, laid: AFragmentAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Held("id", payload.id, SameAs(laid.fragment.id, "심은 조각"))]


@dataclass(frozen=True)
class MineArePurgedTheRestFail(Then[SomeFragmentsAndACaller, BulkPurged]):
    """자기 것은 지워진 목록에, 남의 것과 없는 id는 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "자기 것은 지워진 목록에, 남의 것과 없는 id는 실패 목록에 온다"

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[BulkPurged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "items",
                list(payload.items),
                SameAs[list[UUID]]([one.id for one in laid.mine], "심은 자기 조각들"),
            ),
            Same("failed", len(payload.failed), 2),
            Held[UUID | None](
                "failed[0].id",
                payload.failed[0].id if payload.failed else None,
                SameAs[UUID | None](laid.theirs.id, "심은 남의 조각"),
            ),
            Skipped("failed[*].message", "이유는 글로 오고, 글은 바뀌어도 되는 값이다"),
        ]


@dataclass(frozen=True)
class BothArePurgedTheMissingFails(Then[SomeFragmentsAndACaller, BulkPurged]):
    """둘은 지워진 목록에, 없는 id는 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "있는 둘은 지워진 목록에, 없는 id는 실패 목록에 온다"

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[BulkPurged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "items",
                list(payload.items),
                SameAs[list[UUID]]([*(one.id for one in laid.mine), laid.theirs.id], "심은 조각들"),
            ),
            Same("failed", len(payload.failed), 1),
            Skipped("failed[*].message", "이유는 글로 오고, 글은 바뀌어도 되는 값이다"),
        ]


@dataclass(frozen=True)
class TheGrantedUserPurgesTheirOwn(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment"

    @override
    def describe(self) -> str:
        return "자기 조각 하나가 있고 자기 스코프에 지우기 권한을 받은 사용자가 지우면, 지운 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AnotherUsersFragmentIsRefused(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment"

    @override
    def describe(self) -> str:
        return "다른 사용자의 조각을 자기 스코프에만 지우기 권한을 받은 사용자가 지우면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(whose=Whose.ANOTHERS, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReadingIsNotEnoughToPurge(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-alone-may-not-purge-their-fragment"

    @override
    def describe(self) -> str:
        return "자기 조각에 읽기 권한만 받은 사용자가 지우면, 권한 부족으로 거부된다. 지우기는 읽기와 다른 문이다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무것도 갖지 않은 id를 지우면, 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging(other=uuid4())

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class MixedIdsArePurgedEach(
    Scenario[SeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]
):
    @override
    def summary(self) -> str:
        return "mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에만 지우기 권한을 받은 사용자가 자기 조각 둘, 다른 사용자의 조각, 없는 "
            "id를 한 번에 지우면, 자기 둘은 지워진 목록에, 남의 것과 없는 id는 실패 목록에 이유를 "
            "달고 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(mine=2, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]:
        return PurgingMany()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, BulkPurged]:
        return MineArePurgedTheRestFail()


@dataclass(frozen=True)
class TheSuperadminPurgesBoth(
    Scenario[SeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-both-and-a-missing-id-fails-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 조각 둘과 없는 id 하나를 한 번에 지우면, 둘은 지워진 목록에, 없는 id는 실패 목록에 온다"

    @override
    def given(self) -> Given[SeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(mine=1, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]:
        return PurgingMany()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, BulkPurged]:
        return BothArePurgedTheMissingFails()


SCENARIOS: list[PurgingStep] = [
    TheGrantedUserPurgesTheirOwn(),
    AnotherUsersFragmentIsRefused(),
    ReadingIsNotEnoughToPurge(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]

BULK_SCENARIOS: list[BulkStep] = [
    MixedIdsArePurgedEach(),
    TheSuperadminPurgesBoth(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", BULK_SCENARIOS, ids=lambda s: s.summary())
async def test_purging_many(
    scenario: BulkStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
