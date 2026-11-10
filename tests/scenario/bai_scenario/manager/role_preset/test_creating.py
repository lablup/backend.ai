"""프리셋 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry,
)
from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.role_preset import RolePresetCreateConflict
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.role_preset import (
    ENTRIES,
    APresetAndACaller,
    APresetAndSomeone,
    caller_words,
    lay_a_caller_granted,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "made-preset"
"""만들려는 프리셋의 이름. 시나리오가 정한 값이다."""

type CreatingStep = Scenario[TestSeedingSession, Any, RolePresetAdapter, Any]


def _input(name: str) -> CreateRolePresetInput:
    """선택 필드를 모두 채운 프로젝트 스코프 프리셋 입력."""
    return CreateRolePresetInput(
        name=name,
        scope_type=ProjectEntityType(),
        auto_assign=True,
        auto_assign_to_owner=True,
        permissions=[
            RolePermissionPresetEntry.model_validate({
                "entity_type": entity_type,
                "permission": permission,
            })
            for entity_type, permission in ENTRIES
        ],
    )


@dataclass(frozen=True)
class SomeoneGranted(Given[Any, UserData]):
    """프리셋 권한 하나를 받은 일반 사용자 한 명."""

    granted: Permission

    @override
    def describe(self) -> str:
        ko, en = caller_words(UserRole.USER, self.granted)
        return Says(ko, english=en)

    @override
    async def lay(self, seeding: Any) -> UserData:
        caller: UserData = seeding.made(
            await lay_a_caller_granted(seeding, UserRole.USER, self.granted)
        )
        return caller


@dataclass(frozen=True)
class CreatingWithEveryField(When[UserData, RolePresetAdapter, RolePresetNode]):
    """선택 필드를 모두 채운 프로젝트 스코프 프리셋을 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: UserData) -> str:
        return Says(
            f"{laid.username} 이 자동 부여, 소유자 부여, 권한 항목 둘을 채운 "
            "프로젝트 스코프 프리셋을 만듭니다",
            english=(
                f"{laid.username} creates a project-scope preset with auto assign, owner "
                "assignment and two permission entries filled"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: UserData) -> RolePresetNode:
        with ActingAs(laid):
            payload = await adapter.create(_input(MADE))
        return payload.role_preset


@dataclass(frozen=True)
class CreatingUnderTheSeededName(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """이미 있는 프리셋과 같은 이름, 같은 스코프로 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 이미 있는 {laid.preset.name} 과 같은 이름으로 "
            "프로젝트 스코프 프리셋을 만듭니다",
            english=(
                f"{laid.caller.username} creates a project-scope preset under the name "
                f"{laid.preset.name} that already exists"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(_input(laid.preset.name))
        return payload.role_preset


@dataclass(frozen=True)
class TheWholePresetComesBack(Then[UserData, RolePresetNode]):
    """만든 프리셋 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "채운 값을 모두 담은 프리셋 전체가 응답으로 옵니다",
            english="the whole preset carrying every value filled comes back",
        )

    @override
    def look(self, laid: UserData, answered: Answered[RolePresetNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        generated = Says("데이터베이스가 생성합니다", english="the database generates it")
        return [
            Skipped("id", generated),
            Skipped("entity_id", generated),
            Same("name", node.name, MADE),
            Same("scope_type", node.scope_type, str(ProjectEntityType())),
            Same("role_name_template", node.role_name_template, None),
            Same("auto_assign", node.auto_assign, True),
            Same("auto_assign_to_owner", node.auto_assign_to_owner, True),
            Same("deleted", node.deleted, False),
            Same("deleted_at", node.deleted_at, None),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class AUserGrantedCreateMakesAPreset(
    Scenario[TestSeedingSession, UserData, RolePresetAdapter, RolePresetNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-makes-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 만들기 권한을 받은 사용자가 선택 필드를 모두 채워 프리셋을 만들면, "
            "채운 값을 담은 프리셋 전체가 응답으로 옵니다",
            english=(
                "when a user granted create on presets fills every optional field and "
                "creates a preset, the whole preset carrying those values comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, UserData]:
        return SomeoneGranted(Permission.CREATE)

    @override
    def when(self) -> When[UserData, RolePresetAdapter, RolePresetNode]:
        return CreatingWithEveryField()

    @override
    def then(self) -> Then[UserData, RolePresetNode]:
        return TheWholePresetComesBack(self.started)


@dataclass(frozen=True)
class AUserWithoutCreateMayNotMakeAPreset(
    Scenario[TestSeedingSession, UserData, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-without-create-may-not-make-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 읽기 권한만 받은 사용자가 프리셋을 만들려 하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read on presets tries to create a preset, "
                "it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, UserData]:
        return SomeoneGranted(Permission.READ)

    @override
    def when(self) -> When[UserData, RolePresetAdapter, RolePresetNode]:
        return CreatingWithEveryField()

    @override
    def then(self) -> Then[UserData, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ATakenNameIsRefused(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-taken-name-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 만들기 권한을 받은 사용자가 이미 있는 프리셋과 같은 이름, 같은 스코프로 "
            "만들려 하면, 이름이 겹쳐 거부됩니다",
            english=(
                "when a user granted create on presets creates a preset under the name "
                "and scope of one that already exists, it is rejected as a name conflict"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(granted=Permission.CREATE)

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return CreatingUnderTheSeededName()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(RolePresetCreateConflict)


SCENARIOS: list[CreatingStep] = [
    AUserGrantedCreateMakesAPreset(started=datetime.now(UTC)),
    AUserWithoutCreateMayNotMakeAPreset(),
    ATakenNameIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: RolePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
