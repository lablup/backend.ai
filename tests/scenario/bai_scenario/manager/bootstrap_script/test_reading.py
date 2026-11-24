"""자기 bootstrap script 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.bootstrap_script.response import BootstrapScriptNode
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.bootstrap_script import (
    BootstrapScriptHolder,
    SomeoneWithBootstrapScripts,
    TheBootstrapScriptNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class ReadingMyDefaultScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    """자기 default script 를 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 default bootstrap script 를 id 로 읽습니다",
            english=f"{laid.caller.username} reads their default bootstrap script by id",
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> BootstrapScriptNode:
        with ActingAs(laid.caller):
            payload = await adapter.get(laid.default.script_id)
        return payload.bootstrap_script


@dataclass(frozen=True)
class AUserGrantedReadReadsTheirScript(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-their-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 읽으면, 그 script 가 응답으로 옵니다",
            english="when a user granted READ on their own user reads their bootstrap script by id, that script comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]:
        return ReadingMyDefaultScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptNode]:
        return TheBootstrapScriptNode(started=self.started, default=True)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirScript(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 id 로 읽으려 하면, script 가 있는지 알려 주지 않는 답으로 거부됩니다",
            english="when a user granted nothing tries to read their bootstrap script by id, it is rejected with an answer that does not tell whether the script exists",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts()

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]:
        return ReadingMyDefaultScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptNode]:
        return TheCallIsRefused(GenericBadRequest)


type Step = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode
]

SCENARIOS: list[Step] = [
    AUserGrantedReadReadsTheirScript(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadTheirScript(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
