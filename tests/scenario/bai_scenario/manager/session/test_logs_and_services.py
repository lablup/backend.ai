"""세션의 컨테이너 로그와 서비스 시작과 종료."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.session.request import (
    ShutdownSessionServiceInput,
    StartSessionServiceInput,
)
from ai.backend.common.dto.manager.v2.session.response import SessionLogsPayload
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import ServiceUnavailable
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
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
)
from bai_scenario.fakes.agent import CONTAINER_LOG
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Logs = SessionLogsPayload


@dataclass(frozen=True)
class ReadingTheLogs(When[LaidSessionAndCaller, SessionAdapter, Logs]):
    @override
    def operation(self) -> str:
        return "get_logs"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 컨테이너 로그를 읽습니다",
            english=f"{laid.caller.username} reads the container log of {laid.session.name}",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Logs:
        with ActingAs(laid.caller):
            return await adapter.get_logs(
                laid.session.id, str(laid.session.access_key or "")
            )


@dataclass(frozen=True)
class ShuttingTheServiceDown(When[LaidSessionAndCaller, SessionAdapter, None]):
    service: str = "jupyter"

    @override
    def operation(self) -> str:
        return "shutdown_service"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 서비스를 종료합니다",
            english=f"{laid.caller.username} shuts a service of {laid.session.name} down",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> None:
        with ActingAs(laid.caller):
            return await adapter.shutdown_service(
                laid.session.id,
                ShutdownSessionServiceInput(service=self.service),
                str(laid.session.access_key or ""),
            )


@dataclass(frozen=True)
class StartingTheService(When[LaidSessionAndCaller, SessionAdapter, Any]):
    service: str = "jupyter"

    @override
    def operation(self) -> str:
        return "start_service"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 서비스를 시작합니다",
            english=f"{laid.caller.username} starts a service of {laid.session.name}",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Any:
        with ActingAs(laid.caller):
            return await adapter.start_service(
                laid.session.id, StartSessionServiceInput(service=self.service)
            )


@dataclass(frozen=True)
class TheContainerLogComesBack(Then[LaidSessionAndCaller, Logs]):
    @override
    def says(self) -> str:
        return Says(
            "에이전트가 준 컨테이너 로그가 그대로 반환됩니다",
            english="the container log the agent answered comes back as it is",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Logs]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Same("logs", payload.logs, CONTAINER_LOG)]


@dataclass(frozen=True)
class NothingComesBack(Then[LaidSessionAndCaller, None]):
    @override
    def says(self) -> str:
        return Says(
            "호출이 아무것도 반환하지 않고 예외도 없습니다",
            english="the call answers nothing and raises nothing",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[None]) -> list[Verdict]:
        if answered.raised is not None:
            return [Same("raised", answered.raised, None)]
        return [Same("answered", answered.response, None)]


@dataclass(frozen=True)
class ReadingTheLogsOfASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Logs]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"the-container-log-of-a-session-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 컨테이너 로그를 읽으면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing reads the container log of a session, the call is "
                    "rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 컨테이너 로그를 읽으면, "
            "에이전트가 준 로그가 반환됩니다",
            english=(
                "when a user granted session read in the project reads the container log of a "
                "session, the log the agent answered comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Logs]:
        return ReadingTheLogs()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Logs]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheContainerLogComesBack()


@dataclass(frozen=True)
class ShuttingDownAService(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, None]
):
    granted: bool = True

    @override
    def summary(self) -> str:
        who = "granted" if self.granted else "granted-nothing"
        return f"shutting-down-a-service-{who}"

    @override
    def describe(self) -> str:
        if not self.granted:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 서비스를 종료하려 하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing shuts a service of a session down, the call is "
                    "rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 soft delete 권한을 받은 사용자가 세션의 서비스를 종료하면, "
            "호출이 아무것도 반환하지 않고 끝납니다",
            english=(
                "when a user granted session soft delete in the project shuts a service of a "
                "session down, the call answers nothing"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        if not self.granted:
            return ASessionWithAKernelAndSomeone(granted=Granted.NOTHING)
        return ASessionWithAKernelAndSomeone(permission=Permission.SOFT_DELETE)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, None]:
        return ShuttingTheServiceDown()

    @override
    def then(self) -> Then[LaidSessionAndCaller, None]:
        if not self.granted:
            return TheCallIsRefused(NotEnoughPermission)
        return NothingComesBack()


@dataclass(frozen=True)
class StartingAService(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Any]
):
    granted: bool = True

    @override
    def summary(self) -> str:
        who = "granted" if self.granted else "granted-nothing"
        return f"starting-a-service-{who}"

    @override
    def describe(self) -> str:
        if not self.granted:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 서비스를 시작하려 하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing starts a service of a session, the call is "
                    "rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 생성 권한을 받은 사용자가 프록시 주소가 없는 자원 그룹의 세션에서 "
            "서비스를 시작하려 하면, 프록시가 없어서 거부됩니다",
            english=(
                "when a user granted session create in the project starts a service of a session "
                "whose resource group has no proxy address, the call is rejected as unavailable"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        if not self.granted:
            return ASessionWithAKernelAndSomeone(granted=Granted.NOTHING)
        return ASessionWithAKernelAndSomeone(permission=Permission.CREATE)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Any]:
        return StartingTheService()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Any]:
        if not self.granted:
            return TheCallIsRefused(NotEnoughPermission)
        return TheCallIsRefused(ServiceUnavailable)


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    ReadingTheLogsOfASession(granted=Granted.THE_PROJECT),
    ReadingTheLogsOfASession(granted=Granted.NOTHING),
    ShuttingDownAService(granted=True),
    ShuttingDownAService(granted=False),
    StartingAService(granted=False),
    StartingAService(granted=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_logs_and_services(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
