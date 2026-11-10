"""유휴 검사기 생성 — global 역할 게이트를 거친다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.idle_checker.types import CheckerType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    IdleCheckerSpecInputDTO,
    SessionLifetimeSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import IdleCheckerNode
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerInputTypeDTO
from ai.backend.common.types import SessionTypes
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.idle_checker import CheckersAndACaller
from bai_scenario.components.system import lay_a_caller
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CreatingStep = Scenario[
    TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode
]

MAX_LIFETIME_SECONDS = 7200


@dataclass(frozen=True)
class CreatingAChecker(When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]):
    """세션 수명 검사기를 하나 만든다."""

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 세션 수명 {MAX_LIFETIME_SECONDS}초짜리 검사기를 만듭니다",
            english=(
                f"{laid.caller.username} creates a checker ending sessions after "
                f"{MAX_LIFETIME_SECONDS} seconds"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> IdleCheckerNode:
        request = CreateIdleCheckerInput(
            name="created-checker",
            checker_type=IdleCheckerInputTypeDTO.SESSION_LIFETIME,
            target_session_types=[SessionTypes.INTERACTIVE],
            checker_spec=IdleCheckerSpecInputDTO(
                session_lifetime=SessionLifetimeSpecInputDTO(
                    max_lifetime_seconds=MAX_LIFETIME_SECONDS
                )
            ),
        )
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(request)
        return payload.idle_checker


@dataclass(frozen=True)
class TheCreatedCheckerNode(Then[CheckersAndACaller, IdleCheckerNode]):
    """방금 만든 검사기가 요청에서 지정한 값 그대로 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "생성한 검사기 전체가 반환됩니다",
            english="the whole checker just created comes back",
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[IdleCheckerNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("name", node.name, "created-checker"),
            Same("description", node.description, None),
            Same("checker_type", node.checker_type.value, CheckerType.SESSION_LIFETIME.value),
            Same("target_session_types", node.target_session_types, [SessionTypes.INTERACTIVE]),
            Same("initial_grace_period_seconds", node.initial_grace_period_seconds, 0),
            Same("spec.type", node.spec.type.value, "session_lifetime"),
            Same(
                "spec.session_lifetime.max_lifetime_seconds",
                node.spec.session_lifetime.max_lifetime_seconds
                if node.spec.session_lifetime is not None
                else None,
                MAX_LIFETIME_SECONDS,
            ),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
            Held("updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class TheSuperadminMakesAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 세션 수명 검사기를 만들면, "
            "요청에서 지정한 값 그대로 반환됩니다",
            english=(
                "the operation is gated by the global role, so when the superadmin creates "
                "a session lifetime checker, it comes back with the values the request named"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]:
        return CreatingAChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, IdleCheckerNode]:
        return TheCreatedCheckerNode(started=self.started)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotMakeAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 만들면 "
            "역할 부족으로 거부됩니다",
            english=(
                "the operation is gated by the global role, so when a user who is not the "
                "superadmin creates a checker, it is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]:
        return CreatingAChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, IdleCheckerNode]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class SomeoneAlone(Given[Any, CheckersAndACaller]):
    """검사기 없이 호출자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return Says("유휴 검사기 없이 호출자 한 명", english="no idle checker and one caller")

    @override
    async def lay(self, seeding: Any) -> CheckersAndACaller:
        caller = await lay_a_caller(seeding, self.role)
        return CheckersAndACaller(laid=(), caller=seeding.made(caller))


SCENARIOS: list[CreatingStep] = [
    TheSuperadminMakesAChecker(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotMakeAChecker(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
