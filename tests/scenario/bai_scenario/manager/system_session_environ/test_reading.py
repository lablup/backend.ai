"""시스템 세션 환경변수 여러 id 조회와 값 출처 목록."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.components.system_session_environ import (
    EveryIdIsRefused,
    Loaded,
    ManyEnvironsAndACaller,
    ManyEnvironsAndSomeone,
    TheOrderIsKept,
    TheValueSourcesAreListed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_ID = uuid4()

type ReadingStep = Scenario[TestSeedingSession, Any, SystemSessionEnvironAdapter, Any]


@dataclass(frozen=True)
class ReadingMany(When[ManyEnvironsAndACaller, SystemSessionEnvironAdapter, Loaded]):
    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: ManyEnvironsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 번에 "
            "조회합니다",
            english=(
                f"{laid.caller.username} loads two rows seeded in advance and one id that does "
                "not exist at once"
            ),
        )

    def ids(self, laid: ManyEnvironsAndACaller) -> list[SystemSessionEnvironID]:
        return [
            SystemSessionEnvironID(laid.laid[0].id),
            SystemSessionEnvironID(MISSING_ID),
            SystemSessionEnvironID(laid.laid[1].id),
        ]

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: ManyEnvironsAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids(self.ids(laid))


@dataclass(frozen=True)
class ListingValueSources(When[ACaller, SystemSessionEnvironAdapter, list[str]]):
    anonymous: bool = False

    @override
    def operation(self) -> str:
        return "public_list_value_sources"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 매니저가 제공하는 값 출처를 읽습니다",
            english=f"{laid.caller.username} reads the value sources the manager provides",
        )

    @override
    async def call(self, adapter: SystemSessionEnvironAdapter, laid: ACaller) -> list[str]:
        if self.anonymous:
            payload = await adapter.public_list_value_sources()
            return payload.items
        with ActingAs(laid.caller):
            payload = await adapter.public_list_value_sources()
            return payload.items


@dataclass(frozen=True)
class AUserGrantedReadReadsManyInOrder(
    Scenario[TestSeedingSession, ManyEnvironsAndACaller, SystemSessionEnvironAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-several-environs-in-the-requested-order"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 읽기 권한을 받은 사용자가 미리 저장한 행 둘과 존재하지 않는 id 하나를 한 "
            "번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다",
            english=(
                "when a user granted read permission in public loads two rows seeded in advance "
                "and one id that does not exist at once, the two come back in the requested order "
                "and the entry for the id that does not exist is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyEnvironsAndACaller, SystemSessionEnvironAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyEnvironsAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryId(
    Scenario[TestSeedingSession, ManyEnvironsAndACaller, SystemSessionEnvironAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 id 여럿을 한 번에 조회하면, 요청 전체가 거부되는 대신 "
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads several ids at once, instead of rejecting the "
                "whole request, every entry comes back holding a rejection for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone()

    @override
    def when(self) -> When[ManyEnvironsAndACaller, SystemSessionEnvironAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyEnvironsAndACaller, Loaded]:
        return EveryIdIsRefused()


@dataclass(frozen=True)
class AnyUserReadsTheValueSources(
    Scenario[
        TestSeedingSession,
        ACaller,
        SystemSessionEnvironAdapter,
        list[str],
    ]
):
    @override
    def summary(self) -> str:
        return "any-authenticated-user-reads-the-value-sources"

    @override
    def describe(self) -> str:
        return Says(
            "인증된 사용자면 누구나 매니저가 제공하는 값 출처 목록을 읽을 수 있습니다",
            english="any authenticated user can read the list of value sources the manager provides",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(
        self,
    ) -> When[ACaller, SystemSessionEnvironAdapter, list[str]]:
        return ListingValueSources()

    @override
    def then(
        self,
    ) -> Then[ACaller, list[str]]:
        return TheValueSourcesAreListed()


@dataclass(frozen=True)
class ACallWithNoCallerIsRefused(
    Scenario[
        TestSeedingSession,
        ACaller,
        SystemSessionEnvironAdapter,
        list[str],
    ]
):
    @override
    def summary(self) -> str:
        return "a-call-with-no-caller-is-refused-the-value-sources"

    @override
    def describe(self) -> str:
        return Says(
            "호출자 없이 값 출처 목록을 읽으려 하면 거부됩니다. 이 호출은 인증만 검사합니다",
            english=(
                "when the value source list is read with no caller, it is rejected. This call "
                "checks authentication alone"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(
        self,
    ) -> When[ACaller, SystemSessionEnvironAdapter, list[str]]:
        return ListingValueSources(anonymous=True)

    @override
    def then(
        self,
    ) -> Then[ACaller, list[str]]:
        return TheCallIsRefused(UserNotFound)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedReadReadsManyInOrder(),
    AUserGrantedNothingIsRefusedOnEveryId(),
    AnyUserReadsTheValueSources(),
    ACallWithNoCallerIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
