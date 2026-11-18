"""유휴 검사기 수정 — global 역할 게이트를 거친다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerSpecInputDTO,
    NetworkTimeoutSpecInputDTO,
    UpdateIdleCheckerInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import IdleCheckerNode
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.idle_checker import CheckersAndACaller, SomeCheckersAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingStep = Scenario[
    TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode
]

NEW_MAX_LIFETIME_SECONDS = 5400


@dataclass(frozen=True)
class EditingTheLaidChecker(When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]):
    """미리 저장한 검사기의 검사 규격을 네트워크 비활성 검사로 바꾼다."""

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 검사기 {laid.laid[0].name}의 규격을 "
            f"네트워크 비활성 {NEW_MAX_LIFETIME_SECONDS}초로 바꿉니다",
            english=(
                f"{laid.caller.username} changes the checker {laid.laid[0].name} to the "
                f"network timeout checker of {NEW_MAX_LIFETIME_SECONDS} seconds"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> IdleCheckerNode:
        request = UpdateIdleCheckerInput(
            id=laid.laid[0].id,
            checker_spec=IdleCheckerSpecInputDTO(
                network=NetworkTimeoutSpecInputDTO(
                    max_network_inactivity_seconds=NEW_MAX_LIFETIME_SECONDS
                )
            ),
        )
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(request)
        return payload.idle_checker


@dataclass(frozen=True)
class TheEditedCheckerNode(Then[CheckersAndACaller, IdleCheckerNode]):
    """수정한 검사기가 바뀐 규격으로 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "수정한 검사기 전체가 반환됩니다",
            english="the whole checker edited comes back",
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[IdleCheckerNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Held[UUID](
                "id",
                node.id,
                SameAs(
                    laid.laid[0].id,
                    Says("준비한 검사기", english="the checker laid"),
                ),
            ),
            Held[UUID](
                "entity_id",
                node.entity_id,
                SameAs(
                    laid.laid[0].id,
                    Says("준비한 검사기", english="the checker laid"),
                ),
            ),
            Same("name", node.name, laid.laid[0].name),
            Same("description", node.description, laid.laid[0].description),
            Same("checker_type", node.checker_type.value, "network_timeout"),
            Same(
                "target_session_types", node.target_session_types, laid.laid[0].target_session_types
            ),
            Same("initial_grace_period_seconds", node.initial_grace_period_seconds, 0),
            Same("spec.type", node.spec.type.value, "network_timeout"),
            Same(
                "spec.network.max_network_inactivity_seconds",
                node.spec.network.max_network_inactivity_seconds
                if node.spec.network is not None
                else None,
                NEW_MAX_LIFETIME_SECONDS,
            ),
            Skipped(
                "created_at",
                Says("수정 전에 기록된 시각", english="the time written before the edit"),
            ),
            Held("updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class TheSuperadminEditsAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 검사기의 규격을 바꾸면, "
            "바뀐 규격 그대로 반환됩니다",
            english=(
                "the operation is gated by the global role, so when the superadmin changes "
                "a checker, it comes back with the changed spec"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]:
        return EditingTheLaidChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, IdleCheckerNode]:
        return TheEditedCheckerNode(started=self.started)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotEditAChecker(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검사기를 바꾸면 "
            "역할 부족으로 거부됩니다",
            english=(
                "the operation is gated by the global role, so when a user who is not the "
                "superadmin edits a checker, it is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, IdleCheckerNode]:
        return EditingTheLaidChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, IdleCheckerNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsAChecker(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotEditAChecker(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
