"""세션의 할당을 id로 일괄 읽기 — 대표 성공과 대표 실패."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.session import (
    APendingSessionAndACaller,
    APendingSessionAndSomeoneReadingIt,
    SessionReader,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[ResourceAllocationGQLDTO | Exception]
type LoadStep = Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Answer]


@dataclass(frozen=True)
class LoadingTheSessionsAllocation(When[APendingSessionAndACaller, SessionAdapter, Answer]):
    """그 세션 id 하나의 할당을 일괄 읽기로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_session"

    @override
    def describe(self, laid: APendingSessionAndACaller) -> str:
        return f"{laid.caller.username}이 대기 세션의 할당을 일괄 읽음"

    @override
    async def call(self, adapter: SessionAdapter, laid: APendingSessionAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_session([SessionID(laid.session.id)])


@dataclass(frozen=True)
class AnEmptyAllocation(Then[APendingSessionAndACaller, Answer]):
    """그 세션이 빈 할당으로 온다."""

    @override
    def says(self) -> str:
        return "그 세션이 빈 할당으로 온다"

    @override
    def look(self, laid: APendingSessionAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, ResourceAllocationGQLDTO):
            seen += [
                Same("[0].requested.entries", first.requested.entries, []),
                Same("[0].used.entries", first.used.entries, []),
                Same("[0].allocated.entries", first.allocated.entries, []),
            ]
        else:
            seen.append(Same("[0]", type(first).__name__, "ResourceAllocationGQLDTO"))
        return seen


@dataclass(frozen=True)
class ARefusal(Then[APendingSessionAndACaller, Answer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return "그 자리는 권한 부족으로 거부된다"

    @override
    def look(self, laid: APendingSessionAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AProjectReaderLoadsItsSessionsAllocation(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-session-read-in-the-project-loads-its-sessions-allocation"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 범위에서 세션 조회 권한을 받은 사용자가 그 프로젝트의 세션 할당을 일괄 읽기로 "
            "읽으면, 할당 행이 없는 그 세션은 빈 할당으로 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeoneReadingIt(who=SessionReader.PROJECT_GRANTEE)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Answer]:
        return LoadingTheSessionsAllocation()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Answer]:
        return AnEmptyAllocation()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedTheAllocation(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-the-allocation"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 세션 할당을 일괄 읽기로 읽으면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeoneReadingIt(who=SessionReader.NOBODY_GRANTED)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Answer]:
        return LoadingTheSessionsAllocation()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Answer]:
        return ARefusal()


SCENARIOS: list[LoadStep] = [
    AProjectReaderLoadsItsSessionsAllocation(),
    AUserGrantedNothingIsRefusedTheAllocation(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allocation_loading(
    scenario: LoadStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
