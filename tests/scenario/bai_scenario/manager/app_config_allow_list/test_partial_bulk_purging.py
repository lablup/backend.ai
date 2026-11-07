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
from ai.backend.manager.data.permission.types import Permission
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
        besides_ko = "와 존재하지 않는 ID" if self.missing else ""
        besides_en = " and a missing ID" if self.missing else ""
        return Says(
            f"{laid.caller.username}이 allow_list 둘{besides_ko}를 한 번에 영구 삭제합니다",
            english=(f"{laid.caller.username} purges both allow_lists{besides_en} in one call"),
        )

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
        return Says(
            "allow_list 둘은 처리된 목록에, 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "both allow_lists come back in the processed list, and the missing ID comes "
                "back in the failed list because there is no such target"
            ),
        )

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]](
                    [laid.first.id, laid.second.id],
                    Says("준비한 ID 둘", english="the two IDs seeded in advance"),
                ),
            ),
            Same("failed count", len(payload.failed), 1),
        ]
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        MISSING,
                        Says("요청에 넣은 없는 ID", english="the missing ID in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NeitherIsPurged(Then[TwoEntriesAndACaller, Purged]):
    """처리된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "처리된 allow_list 없이 둘 다 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "no allow_list is processed and both come back in the failed list "
                "for lack of permission"
            ),
        )

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
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(entry.id, Says("준비한 ID", english="the ID seeded in advance")),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class BothArePurged(Then[TwoEntriesAndACaller, Purged]):
    """둘은 처리된 목록에 오고, 실패 목록은 비어 있다."""

    @override
    def says(self) -> str:
        return Says(
            "allow_list 둘은 처리된 목록에 오고, 실패한 것은 없습니다",
            english="both allow_lists come back in the processed list and none failed",
        )

    @override
    def look(self, laid: TwoEntriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("successes count", len(payload.successes), 2),
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]](
                    [laid.first.id, laid.second.id],
                    Says("준비한 ID 둘", english="the two IDs seeded in advance"),
                ),
            ),
            Same("failed", payload.failed, []),
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesBothAndIsToldOfTheMissing(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 allow_list 둘과 존재하지 않는 ID 를 한 번에 영구 삭제하면, 둘은 처리된 "
            "목록에 오고 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges both allow_lists and a missing ID in one call, "
                "the two come back in the processed list and the missing ID comes back in the "
                "failed list because there is no such target"
            ),
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
class AWriterPurgesBoth(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-in-global-purges-both-entries-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "global 스코프에서 허용 목록 항목에 대한 영구 삭제 권한을 받은 일반 사용자가 "
            "allow_list 둘을 한 번에 영구 삭제하면, 둘 다 처리된 목록에 오고 실패한 것은 없습니다",
            english=(
                "when a regular user granted the purge permission on allow-list entries in the "
                "global scope purges both allow_lists in one call, both come back in the "
                "processed list and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoEntriesAndACaller]:
        return TwoEntriesAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]:
        return PurgingBoth()

    @override
    def then(self) -> Then[TwoEntriesAndACaller, Purged]:
        return BothArePurged()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, TwoEntriesAndACaller, AppConfigAllowListAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-entries"

    @override
    def describe(self) -> str:
        return Says(
            "권한이 없는 일반 사용자가 allow_list 둘을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 "
            "둘 다 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a plain user without permission tries to purge both allow_lists in one "
                "call, none is deleted and both come back in the failed list for lack of "
                "permission"
            ),
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
    AWriterPurgesBoth(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
