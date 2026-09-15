"""배포 옵션 갈아끼우기 — 준 것이 통째로 남고, 등록된 처리기만 받는다.

처리기 이름은 등록된 처리기에서 읽는다. 이 모듈이 적는 이름은 등록되지 않은 하나뿐이다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import ADeploymentAndACaller, ADeploymentInThatPlace
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.deployment.request import ReplaceDeploymentOptionsInput
from ai.backend.common.dto.manager.v2.deployment.response import ReplaceDeploymentOptionsPayload
from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentHandlerOptionsInput,
    DeploymentOptionsInput,
)
from ai.backend.common.dto.manager.v2.session_options.request import (
    HandlerOptionsEntryInput,
    HandlerOptionsInput,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)

REGISTERED = CheckReplicaDeploymentHandler.name()
UNREGISTERED = "no-such-handler"
WAITS = 600
RETRIES = 3

type Entry = tuple[str, int | None, int | None]
type OptionsStep = Scenario[
    SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
]


@dataclass(frozen=True)
class Replacing(When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]):
    """배포의 옵션을 준 것으로 갈아끼운다."""

    entries: tuple[Entry, ...] = ()

    @override
    def operation(self) -> str:
        return "replace_options"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        if not self.entries:
            given = "기본값만 담아"
        else:
            given = f"처리기별 설정 {', '.join(name for name, _, _ in self.entries)}을 담아"
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 옵션을 {given} 갈아끼움"

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller
    ) -> ReplaceDeploymentOptionsPayload:
        asked = ReplaceDeploymentOptionsInput(
            options=DeploymentOptionsInput(
                handler_options=DeploymentHandlerOptionsInput(
                    default=HandlerOptionsInput(timeout_sec=WAITS, max_retry_count=RETRIES),
                    by_handler=[
                        HandlerOptionsEntryInput(
                            handler_name=name, timeout_sec=waits, max_retry_count=retries
                        )
                        for name, waits, retries in self.entries
                    ],
                )
            )
        )
        with ActingAs(laid.caller):
            return await adapter.replace_options(laid.deployment.id, asked)


@dataclass(frozen=True)
class TheOptionsAreReplaced(Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]):
    """준 옵션이 통째로 온다. 배포 전체가 아니라 옵션만 싣는다."""

    entries: tuple[Entry, ...] = field(default_factory=tuple)

    @override
    def says(self) -> str:
        return "갈아끼운 옵션만 온다"

    @override
    def look(
        self,
        laid: ADeploymentAndACaller,
        answered: Answered[ReplaceDeploymentOptionsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        handler = payload.options.handler_options
        return [
            Held("deployment_id", payload.deployment_id, SameAs(laid.deployment.id, "심은 배포")),
            Same("options.handler_options.default.timeout_sec", handler.default.timeout_sec, WAITS),
            Same(
                "options.handler_options.default.max_retry_count",
                handler.default.max_retry_count,
                RETRIES,
            ),
            Same(
                "options.handler_options.by_handler",
                [(e.handler_name, e.timeout_sec, e.max_retry_count) for e in handler.by_handler],
                sorted(self.entries),
            ),
        ]


@dataclass(frozen=True)
class WhatIsGivenBecomesTheOptions(
    Scenario[
        SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-replaces-the-options-whole"

    @override
    def describe(self) -> str:
        return (
            "수정 권한을 받은 사용자가 기본값과 처리기별 설정을 담아 옵션을 갈아끼우면, "
            "준 것이 통째로 새 옵션이 되고 답은 그 옵션만 싣는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]:
        return Replacing(entries=((REGISTERED, None, 1),))

    @override
    def then(self) -> Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]:
        return TheOptionsAreReplaced(entries=((REGISTERED, None, 1),))


@dataclass(frozen=True)
class WhatIsNotGivenDoesNotStay(
    Scenario[
        SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "replacing-with-no-handler-entry-drops-the-inherited-ones"

    @override
    def describe(self) -> str:
        return (
            "물려받은 처리기별 설정이 있는 배포에 기본값만 담아 옵션을 갈아끼우면, "
            "물려받은 설정이 하나도 남지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]:
        return Replacing()

    @override
    def then(self) -> Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]:
        return TheOptionsAreReplaced()


@dataclass(frozen=True)
class AnUnregisteredHandlerIsRefused(
    Scenario[
        SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "naming-an-unregistered-handler-is-refused"

    @override
    def describe(self) -> str:
        return "등록되지 않은 처리기 이름을 담아 옵션을 갈아끼우면, 입력이 틀렸다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]:
        return Replacing(entries=((UNREGISTERED, None, 1),))

    @override
    def then(self) -> Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AHandlerNamedTwiceIsRefused(
    Scenario[
        SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "naming-a-handler-twice-is-refused"

    @override
    def describe(self) -> str:
        return "같은 처리기 이름을 두 번 담아 옵션을 갈아끼우면, 입력이 틀렸다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]:
        return Replacing(entries=((REGISTERED, None, 1), (REGISTERED, None, 2)))

    @override
    def then(self) -> Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class ReadingIsNotEnoughToReplace(
    Scenario[
        SeedingSession, ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-replace-the-options"

    @override
    def describe(self) -> str:
        return "읽기 권한만 받은 사용자가 옵션을 갈아끼우면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[ADeploymentAndACaller, DeploymentAdapter, ReplaceDeploymentOptionsPayload]:
        return Replacing(entries=((REGISTERED, None, 1),))

    @override
    def then(self) -> Then[ADeploymentAndACaller, ReplaceDeploymentOptionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[OptionsStep] = [
    WhatIsGivenBecomesTheOptions(),
    WhatIsNotGivenDoesNotStay(),
    AnUnregisteredHandlerIsRefused(),
    AHandlerNamedTwiceIsRefused(),
    ReadingIsNotEnoughToReplace(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_options(
    scenario: OptionsStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
