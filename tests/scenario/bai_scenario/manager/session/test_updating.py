"""세션 수정."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.session.request import UpdateSessionInput
from ai.backend.common.dto.manager.v2.session.response import UpdateSessionPayload
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_allocation import Granted
from bai_scenario.components.session_reads import (
    ASessionWithAKernelAndSomeone,
    LaidSessionAndCaller,
    session_dump,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Updated = UpdateSessionPayload


@dataclass(frozen=True)
class UpdatingTheSession(When[LaidSessionAndCaller, SessionAdapter, Updated]):
    new_name: str | None = None

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        if self.new_name is None:
            return Says(
                f"{laid.caller.username}이 바꿀 값 없이 세션을 수정 요청합니다",
                english=f"{laid.caller.username} updates the session with no value to change",
            )
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 이름을 바꿉니다",
            english=f"{laid.caller.username} renames the session {laid.session.name}",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Updated:
        with ActingAs(laid.caller):
            return await adapter.update(
                laid.session.id,
                UpdateSessionInput(name=self.new_name),
                str(laid.session.access_key or ""),
            )


@dataclass(frozen=True)
class TheSessionComesBack(Then[LaidSessionAndCaller, Updated]):
    @override
    def says(self) -> str:
        return Says(
            "현재 세션 전체가 저장된 그대로 반환됩니다",
            english="the current session comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Updated]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "session",
                payload.session.model_dump(),
                SameAs(
                    session_dump(laid),
                    Says(
                        "저장된 세션의 전체 정보",
                        english="the whole information of the stored session",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class UpdatingWithNothingToChange(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Updated]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-session-update-with-no-field-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 바꿀 값 없이 세션을 수정 요청하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing updates a session with no value to change, the "
                    "call is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 바꿀 값 없이 세션을 수정 요청하면, "
            "현재 세션 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project updates a session with no "
                "value to change, the current session comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Updated]:
        return UpdatingTheSession()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Updated]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheSessionComesBack()


@dataclass(frozen=True)
class RenamingAWaitingSession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Updated]
):
    @override
    def summary(self) -> str:
        return "renaming-a-session-that-is-not-running-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "그 프로젝트에서 세션 수정 권한을 받은 사용자가 아직 실행 중이 아닌 세션의 이름을 "
            "바꾸려 하면, 실행 중이 아니라서 거부됩니다",
            english=(
                "when a user granted session update in the project renames a session that is "
                "not running, the call is rejected because of its state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=Granted.THE_PROJECT, permission=Permission.UPDATE
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Updated]:
        return UpdatingTheSession(new_name="renamed")

    @override
    def then(self) -> Then[LaidSessionAndCaller, Updated]:
        return TheCallIsRefused(InvalidAPIParameters)


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    UpdatingWithNothingToChange(granted=Granted.THE_PROJECT),
    UpdatingWithNothingToChange(granted=Granted.NOTHING),
    RenamingAWaitingSession(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_updating(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
