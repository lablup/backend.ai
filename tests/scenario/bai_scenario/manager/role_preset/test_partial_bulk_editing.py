"""프리셋 여럿 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.role_preset.request import (
    PartialBulkUpdateRolePresetItemInput,
    PartialBulkUpdateRolePresetsInput,
    UpdateRolePresetBody,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
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
from bai_scenario.components.domain import Mentions
from bai_scenario.components.role_preset import (
    AProjectAndADomainPresetAndSomeone,
    EveryTargetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NothingIsProcessed,
    OnlyTheFirstPresetComesBack,
    PresetLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Edited = PartialBulkPayload[RolePresetNode]
type EditingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]


@dataclass(frozen=True)
class TurningAutoAssignOnForEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Edited]):
    """대상 프리셋 모두의 자동 부여를 한 번에 켠다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 자동 부여를 한 번에 켭니다",
            english=(
                f"{laid.caller.username} turns auto assign on for {len(laid.laid)} presets at once"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateRolePresetItemInput(
                id=preset.id, input=UpdateRolePresetBody(auto_assign=True)
            )
            for preset in laid.laid
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateRolePresetsInput(items=items))


@dataclass(frozen=True)
class TurningOwnerAssignOnForEvery(When[ManyPresetsAndACaller, RolePresetAdapter, Edited]):
    """대상 프리셋 모두의 소유자 부여를 한 번에 켠다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 프리셋 {len(laid.laid)}개의 소유자 부여를 한 번에 켭니다",
            english=(
                f"{laid.caller.username} turns on owner assignment of "
                f"{len(laid.laid)} presets at once"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateRolePresetItemInput(
                id=preset.id, input=UpdateRolePresetBody(auto_assign_to_owner=True)
            )
            for preset in laid.laid
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateRolePresetsInput(items=items))


@dataclass(frozen=True)
class AUserGrantedUpdateEditsSeveral(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 프리셋 여럿의 자동 부여를 한 번에 켜면, 모두 새 값으로 "
            "오고 실패한 것은 없습니다",
            english=(
                "when a user granted update on presets turns auto assign on for several "
                "presets at once, all of them come back with the new value and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningAutoAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryTargetComesBack(PresetLook(self.started, auto_assign=True))


@dataclass(frozen=True)
class AUserWithoutUpdateEditsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-without-update-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 읽기 권한만 받은 사용자가 프리셋 여럿을 한 번에 수정하려 하면, "
            "수정된 것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted only read on presets tries to edit several presets at once, "
                "none is edited and every one comes back in the failed list for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningAutoAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return NothingIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class OnlyTheProjectPresetTakesOwnerAssign(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "only-the-project-preset-takes-owner-assign"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 프로젝트 스코프와 도메인 스코프 프리셋의 소유자 부여를 "
            "한 번에 켜면, "
            "프로젝트 스코프 프리셋만 수정되고 도메인 스코프 프리셋은 실패 목록에 옵니다",
            english=(
                "turning on owner assignment of project-scope and domain-scope presets at "
                "once edits only the project-scope preset, and the domain-scope preset "
                "comes back in the failed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return AProjectAndADomainPresetAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return TurningOwnerAssignOnForEvery()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return OnlyTheFirstPresetComesBack(PresetLook(self.started, auto_assign_to_owner=True))


@dataclass(frozen=True)
class RenamingTheFirstToTheSecondName(When[ManyPresetsAndACaller, RolePresetAdapter, Edited]):
    """첫 프리셋의 이름을 둘째 프리셋의 이름으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        first, second = laid.laid
        return Says(
            f"{laid.caller.username} 이 {first.name} 의 이름을 같은 스코프의 {second.name} 로 바꿉니다",
            english=(
                f"{laid.caller.username} renames {first.name} to {second.name} in the same scope"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        first, second = laid.laid
        items = [
            PartialBulkUpdateRolePresetItemInput(
                id=first.id, input=UpdateRolePresetBody(name=second.name)
            )
        ]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(PartialBulkUpdateRolePresetsInput(items=items))


@dataclass(frozen=True)
class TheRenamedOneFailsOnTheName(Then[ManyPresetsAndACaller, Edited]):
    """이름을 바꾼 프리셋이 이름이 겹친다는 이유로 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "수정된 것 없이 이름을 바꾼 프리셋이 이름이 겹친다는 이유로 실패 목록에 옵니다",
            english=(
                "nothing is edited and the renamed preset comes back in the failed list "
                "because the name is taken"
            ),
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), 1),
        ]
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.laid[0].id,
                        Says("이름을 바꾼 프리셋의 id", english="the id of the renamed preset"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("already has this name")),
            ]
        return verdicts


@dataclass(frozen=True)
class ATakenNameFailsTheRename(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-taken-name-fails-the-rename"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 수정 권한을 받은 사용자가 프리셋의 이름을 같은 스코프에 이미 있는 이름으로 "
            "바꾸면, 수정된 것 없이 그 프리셋이 이름이 겹친다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted update on presets renames a preset to a name already "
                "taken in the same scope, nothing is edited and the preset comes back in the "
                "failed list because the name is taken"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Edited]:
        return RenamingTheFirstToTheSecondName()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return TheRenamedOneFailsOnTheName()


SCENARIOS: list[EditingStep] = [
    AUserGrantedUpdateEditsSeveral(started=datetime.now(UTC)),
    AUserWithoutUpdateEditsNone(),
    OnlyTheProjectPresetTakesOwnerAssign(started=datetime.now(UTC)),
    ATakenNameFailsTheRename(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
