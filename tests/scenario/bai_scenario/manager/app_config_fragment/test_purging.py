"""설정 조각 삭제 — 하나씩, 그리고 여럿을 한 번에.

삭제는 허용 목록 항목을 확인하지 않는다. 조각은 허용 목록 항목이 있는 동안만 존재하므로, 있는
조각은 언제나 자기 스코프에서 삭제할 수 있다. 여럿을 삭제하면 원소마다 응답하고, 이 어댑터에는
soft delete가 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    PartialBulkPurgeAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
    PurgeAppConfigFragmentPayload,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.exception import UnreachableError
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
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    AFragmentAndACaller,
    AFragmentAndSomeone,
    SomeFragmentsAndACaller,
    SomeFragmentsAndSomeone,
    Whose,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PurgeAppConfigFragmentPayload
type PurgingStep = Scenario[
    TestSeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged
]
type BulkPurged = PartialBulkPayload[AppConfigFragmentNode]
type BulkStep = Scenario[
    TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged
]


@dataclass(frozen=True)
class Purging(When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]):
    """설정 조각 하나를 삭제한다. id를 지정하지 않으면 미리 만들어 둔 조각을 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AFragmentAndACaller) -> str:
        if self.other is not None:
            return Says(
                f"{laid.caller.username} 이 존재하지 않는 id 를 삭제합니다",
                english=f"{laid.caller.username} deletes a missing id",
            )
        return Says(
            f"{laid.caller.username} 이 {laid.fragment.config_name} 의 조각을 삭제합니다",
            english=f"{laid.caller.username} deletes the fragment of {laid.fragment.config_name}",
        )

    @override
    async def call(self, adapter: AppConfigFragmentAdapter, laid: AFragmentAndACaller) -> Purged:
        wanted = AppConfigFragmentID(self.other) if self.other is not None else laid.fragment.id
        with ActingAs(laid.caller):
            return await adapter.purge(wanted)


@dataclass(frozen=True)
class PurgingMany(When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]):
    """자기 조각들, 남의 조각, 존재하지 않는 id를 한 번에 삭제한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: SomeFragmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 자기 조각 {len(laid.mine)}개, 다른 사용자의 조각, "
            "존재하지 않는 id 를 한 번에 삭제합니다",
            english=(
                f"{laid.caller.username} deletes {len(laid.mine)} own fragments, another user's "
                "fragment and a missing id at once"
            ),
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: SomeFragmentsAndACaller
    ) -> BulkPurged:
        asked = [*(one.id for one in laid.mine), laid.theirs.id, AppConfigFragmentID(uuid4())]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeAppConfigFragmentsInput(ids=asked)
            )


@dataclass(frozen=True)
class ThePurgedOneIsNamed(Then[AFragmentAndACaller, Purged]):
    """삭제한 조각이 무엇인지 id로 응답한다."""

    @override
    def says(self) -> str:
        return Says(
            "삭제한 조각의 id 를 응답합니다",
            english="it answers with the id of the deleted fragment",
        )

    @override
    def look(self, laid: AFragmentAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held(
                "id",
                payload.id,
                SameAs(
                    laid.fragment.id,
                    Says("미리 저장한 조각", english="the fragment made in advance"),
                ),
            )
        ]


@dataclass(frozen=True)
class MineArePurgedTheRestFail(Then[SomeFragmentsAndACaller, BulkPurged]):
    """자기 것은 삭제된 목록에, 남의 것과 없는 id는 실패 목록에 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "자기 것은 삭제된 목록에, 남의 것과 없는 id 는 실패 목록에 반환됩니다",
            english=(
                "the user's own fragments come back in the succeeded list, and another user's "
                "fragment and the missing id come back in the failed list"
            ),
        )

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[BulkPurged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]](
                    [one.id for one in laid.mine],
                    Says(
                        "미리 저장한 자기 조각들",
                        english="the user's own fragments made in advance",
                    ),
                ),
            ),
            Same("failed", len(payload.failed), 2),
            Held[UUID | None](
                "failed[0].id",
                payload.failed[0].id if payload.failed else None,
                SameAs[UUID | None](
                    laid.theirs.id,
                    Says(
                        "미리 저장한 남의 조각",
                        english="another user's fragment made in advance",
                    ),
                ),
            ),
            Skipped(
                "failed[*].message",
                Says(
                    "이유는 문자열로 오고, 문자열은 변경되어도 되는 값입니다",
                    english="the reason comes as a string, and a string is a value that may change",
                ),
            ),
        ]


@dataclass(frozen=True)
class BothArePurgedTheMissingFails(Then[SomeFragmentsAndACaller, BulkPurged]):
    """둘은 삭제된 목록에, 없는 id는 실패 목록에 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "있는 둘은 삭제된 목록에, 없는 id 는 실패 목록에 반환됩니다",
            english=(
                "the two existing fragments come back in the succeeded list, and the missing "
                "id comes back in the failed list"
            ),
        )

    @override
    def look(self, laid: SomeFragmentsAndACaller, answered: Answered[BulkPurged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]](
                    [*(one.id for one in laid.mine), laid.theirs.id],
                    Says(
                        "미리 저장한 조각들",
                        english="the fragments made in advance",
                    ),
                ),
            ),
            Same("failed", len(payload.failed), 1),
            Skipped(
                "failed[*].message",
                Says(
                    "이유는 문자열로 오고, 문자열은 변경되어도 되는 값입니다",
                    english="the reason comes as a string, and a string is a value that may change",
                ),
            ),
        ]


@dataclass(frozen=True)
class TheGrantedUserPurgesTheirOwn(
    Scenario[TestSeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-their-own-scope-purges-their-fragment"

    @override
    def describe(self) -> str:
        return Says(
            "자기 조각 하나가 있고 자기 스코프에 삭제 권한을 받은 사용자가 삭제하면, "
            "삭제한 id 를 담은 응답이 반환됩니다",
            english=(
                "when a user with one own fragment and delete permission on their own scope "
                "deletes it, an answer holding the deleted id comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return ThePurgedOneIsNamed()


@dataclass(frozen=True)
class AnotherUsersFragmentIsRefused(
    Scenario[TestSeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-on-their-own-scope-may-not-purge-another-users-fragment"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사용자의 조각을 자기 스코프에만 삭제 권한을 받은 사용자가 삭제하면, "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted delete permission only on their own scope deletes another "
                "user's fragment, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(whose=Whose.ANOTHERS, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReadingIsNotEnoughToPurge(
    Scenario[TestSeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-alone-may-not-purge-their-fragment"

    @override
    def describe(self) -> str:
        return Says(
            "자기 조각에 읽기 권한만 받은 사용자가 삭제하면, 권한 부족으로 거부됩니다. "
            "삭제는 읽기와 다른 권한을 검사합니다",
            english=(
                "when a user granted only read permission on their own fragment deletes it, "
                "it is rejected for lack of permission. Delete checks a permission other than read"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[TestSeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 삭제하면, 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin deletes a missing id, it is rejected because no such "
                "target exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, Purged]:
        return Purging(other=uuid4())

    @override
    def then(self) -> Then[AFragmentAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class MixedIdsArePurgedEach(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]
):
    @override
    def summary(self) -> str:
        return "mine-anothers-and-a-missing-id-are-each-answered-for-a-plain-user"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프에만 삭제 권한을 받은 사용자가 자기 조각 둘, 다른 사용자의 조각, 없는 "
            "id 를 한 번에 삭제하면, 자기 둘은 삭제된 목록에, 남의 것과 없는 id 는 실패 목록에 "
            "이유와 함께 반환됩니다",
            english=(
                "when a user granted delete permission only on their own scope deletes two own "
                "fragments, another user's fragment and a missing id at once, the two own "
                "fragments come back in the succeeded list and the others come back in the "
                "failed list together with the reason"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(mine=2, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]:
        return PurgingMany()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, BulkPurged]:
        return MineArePurgedTheRestFail()


@dataclass(frozen=True)
class TheSuperadminPurgesBoth(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-both-and-a-missing-id-fails-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 조각 둘과 없는 id 하나를 한 번에 삭제하면, 둘은 삭제된 목록에, "
            "없는 id 는 실패 목록에 반환됩니다",
            english=(
                "when the superadmin deletes two fragments and one missing id at once, the two "
                "come back in the succeeded list and the missing id comes back in the failed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(mine=1, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]:
        return PurgingMany()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, BulkPurged]:
        return BothArePurgedTheMissingFails()


@dataclass(frozen=True)
class PurgingManyAsNobody(When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]):
    """사용자 컨텍스트 없이 한 번에 삭제한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: SomeFragmentsAndACaller) -> str:
        return Says(
            f"사용자 컨텍스트 없이 조각 {len(laid.mine) + 1}개를 한 번에 삭제합니다",
            english=f"deletes {len(laid.mine) + 1} fragments at once without a user context",
        )

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: SomeFragmentsAndACaller
    ) -> BulkPurged:
        asked = [*(one.id for one in laid.mine), laid.theirs.id]
        return await adapter.partial_bulk_purge(
            PartialBulkPurgeAppConfigFragmentsInput(ids=asked)
        )


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]
):
    @override
    def summary(self) -> str:
        return "a-fragment-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "조각들이 있고 사용자 컨텍스트 없이 한 번에 삭제하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when fragments exist and are purged at once without a user context, it is "
                "rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SomeFragmentsAndACaller]:
        return SomeFragmentsAndSomeone(mine=1)

    @override
    def when(self) -> When[SomeFragmentsAndACaller, AppConfigFragmentAdapter, BulkPurged]:
        return PurgingManyAsNobody()

    @override
    def then(self) -> Then[SomeFragmentsAndACaller, BulkPurged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PurgingStep] = [
    TheGrantedUserPurgesTheirOwn(),
    AnotherUsersFragmentIsRefused(),
    ReadingIsNotEnoughToPurge(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]

BULK_SCENARIOS: list[BulkStep] = [
    MixedIdsArePurgedEach(),
    TheSuperadminPurgesBoth(),
    APurgeCarryingNoUserIsRefused(),
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
