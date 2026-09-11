"""id로 설정 조각 조회 — 그 조각 자체에 부여된 권한을 검사한다.

공개 조각은 스코프로 조회할 때는 누구나 볼 수 있지만 id로 조회할 때는 그렇지 않다. 어느
스코프에도 속하지 않아 그 조각 자체에 부여된 역할 말고는 도달하는 역할이 없기 때문이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config_fragment import (
    AFragmentAndACaller,
    AFragmentAndSomeone,
    TheFragmentNode,
    Whose,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.manager.api.adapters.app_config_fragment.adapter import AppConfigFragmentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode
]


@dataclass(frozen=True)
class ReadingById(When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]):
    """id로 조회한다. id를 지정하지 않으면 미리 만들어 둔 조각의 id를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AFragmentAndACaller) -> str:
        called = (
            "존재하지 않는 id" if self.other is not None else f"{laid.fragment.config_name}의 조각"
        )
        return f"{laid.caller.username}이 {called} 조회"

    @override
    async def call(
        self, adapter: AppConfigFragmentAdapter, laid: AFragmentAndACaller
    ) -> AppConfigFragmentNode:
        wanted = AppConfigFragmentID(self.other) if self.other is not None else laid.fragment.id
        with ActingAs(laid.caller):
            return await adapter.get(wanted)


@dataclass(frozen=True)
class TheGrantedUserReadsTheirOwn(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-their-own-scope-reads-their-fragment-by-id"

    @override
    def describe(self) -> str:
        return "자기 조각 하나가 있고 자기 스코프에 읽기 권한을 받은 사용자가 id로 조회하면, 그 조각 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AFragmentAndACaller, AppConfigFragmentNode]:
        return TheFragmentNode(started=self.started)


@dataclass(frozen=True)
class AnotherUsersFragmentIsRefused(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-their-own-scope-may-not-read-another-users-fragment"

    @override
    def describe(self) -> str:
        return "다른 사용자의 조각을 자기 스코프에만 읽기 권한을 받은 사용자가 id로 조회하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(whose=Whose.ANOTHERS, granted=(Permission.READ,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AFragmentAndACaller, AppConfigFragmentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class APublicFragmentByIdNeedsAGrant(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-public-fragment-by-id"

    @override
    def describe(self) -> str:
        return (
            "공개 조각을 아무 권한도 없는 사용자가 id로 조회하면, 권한 부족으로 거부된다. "
            "스코프로 조회할 때와 반대로, id 조회는 그 조각 자체에 부여된 권한을 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(whose=Whose.PUBLIC)

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AFragmentAndACaller, AppConfigFragmentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsRefusedAsPermission(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에 읽기 권한을 받은 사용자가 존재하지 않는 id로 조회하면, 대상 없음이 "
            "아니라 권한 부족으로 거부된다. 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]:
        return ReadingById(other=uuid4())

    @override
    def then(self) -> Then[AFragmentAndACaller, AppConfigFragmentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 id로 조회하면, 대상을 찾을 수 없다는 이유로 거부된다. "
            "권한 검사를 통과하는 사용자만 이 응답을 본다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFragmentAndACaller]:
        return AFragmentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AFragmentAndACaller, AppConfigFragmentAdapter, AppConfigFragmentNode]:
        return ReadingById(other=uuid4())

    @override
    def then(self) -> Then[AFragmentAndACaller, AppConfigFragmentNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    TheGrantedUserReadsTheirOwn(started=datetime.now(UTC)),
    AnotherUsersFragmentIsRefused(),
    APublicFragmentByIdNeedsAGrant(),
    AnUnknownIdIsRefusedAsPermission(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: AppConfigFragmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
