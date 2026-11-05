"""설정 정의 여럿 영구 삭제하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    PartialBulkPurgeAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_definition import (
    TwoDefinitionsAndACaller,
    TwoDefinitionsAndSomeone,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=1)

type Purged = PartialBulkPayload[AppConfigDefinitionNode]
type PurgingStep = Scenario[
    TestSeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged
]


@dataclass(frozen=True)
class PurgingBoth(When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]):
    """준비한 설정 정의 둘을 한 번에 영구 삭제한다. `missing`이면 없는 ID도 함께 넣는다."""

    missing: bool = False

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: TwoDefinitionsAndACaller) -> str:
        if self.missing:
            return Says(
                f"{laid.caller.username} 이 설정 정의 둘과 존재하지 않는 ID 를 한 번에 영구 삭제합니다",
                english=(
                    f"{laid.caller.username} purges two config definitions and a missing id at once"
                ),
            )
        return Says(
            f"{laid.caller.username} 이 설정 정의 둘을 한 번에 영구 삭제합니다",
            english=f"{laid.caller.username} purges two config definitions at once",
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: TwoDefinitionsAndACaller
    ) -> Purged:
        ids = [laid.first.id, laid.second.id, *((MISSING,) if self.missing else ())]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeAppConfigDefinitionsInput(ids=ids)
            )


@dataclass(frozen=True)
class BothArePurgedTheMissingFails(Then[TwoDefinitionsAndACaller, Purged]):
    """둘은 처리된 목록에, 없는 ID는 대상이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "설정 정의 둘은 처리된 목록에 오고, 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "both config definitions come back in the succeeded list, and the missing id "
                "comes back in the failed list because no such target exists"
            ),
        )

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Held[list[UUID]](
                "successes",
                [node.id for node in payload.successes],
                SameAs[list[UUID]](
                    [laid.first.id, laid.second.id],
                    Says("준비한 ID 둘", english="the two ids prepared"),
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
                        Says("요청에 넣은 없는 ID", english="the missing id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NeitherIsPurged(Then[TwoDefinitionsAndACaller, Purged]):
    """처리된 것 없이 둘 다 권한이 없다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "처리된 설정 정의 없이 둘 다 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "no config definition is processed and both come back in the failed list "
                "for lack of permission"
            ),
        )

    @override
    def look(self, laid: TwoDefinitionsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = (laid.first, laid.second)
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(targets)),
        ]
        for i, (failure, definition) in enumerate(zip(payload.failed, targets, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(definition.id, Says("준비한 ID", english="the id prepared")),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("Insufficient permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class TheSuperadminPurgesBothAndIsToldOfTheMissing(
    Scenario[TestSeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 설정 정의 둘과 존재하지 않는 ID 를 한 번에 영구 삭제하면, 둘은 처리된 "
            "목록에 오고 없는 ID 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two config definitions and a missing id at once, "
                "both come back in the succeeded list and the missing id comes back in the "
                "failed list because no such target exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]:
        return PurgingBoth(missing=True)

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Purged]:
        return BothArePurgedTheMissingFails()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-definitions"

    @override
    def describe(self) -> str:
        return Says(
            "권한이 없는 일반 사용자가 설정 정의 둘을 한 번에 영구 삭제하려 하면, 삭제된 것 없이 "
            "둘 다 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a regular user with no permission tries to purge two config definitions "
                "at once, nothing is purged and both come back in the failed list for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone()

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]:
        return PurgingBoth()

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Purged]:
        return NeitherIsPurged()


@dataclass(frozen=True)
class PurgingBothAsNobody(When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]):
    """사용자 컨텍스트 없이 한 번에 영구 삭제한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: TwoDefinitionsAndACaller) -> str:
        return Says(
            "사용자 컨텍스트 없이 설정 정의 둘을 한 번에 영구 삭제합니다",
            english="purges two config definitions at once without a user context",
        )

    @override
    async def call(
        self, adapter: AppConfigDefinitionAdapter, laid: TwoDefinitionsAndACaller
    ) -> Purged:
        return await adapter.partial_bulk_purge(
            PartialBulkPurgeAppConfigDefinitionsInput(ids=[laid.first.id, laid.second.id])
        )


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-definition-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "설정 정의 둘이 있고 사용자 컨텍스트 없이 한 번에 영구 삭제하면, 호출자를 알 수 없어 "
            "거부됩니다",
            english=(
                "when two config definitions exist and are purged at once without a user "
                "context, it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDefinitionsAndACaller]:
        return TwoDefinitionsAndSomeone()

    @override
    def when(self) -> When[TwoDefinitionsAndACaller, AppConfigDefinitionAdapter, Purged]:
        return PurgingBothAsNobody()

    @override
    def then(self) -> Then[TwoDefinitionsAndACaller, Purged]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesBothAndIsToldOfTheMissing(),
    AUserGrantedNothingPurgesNone(),
    APurgeCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: AppConfigDefinitionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
