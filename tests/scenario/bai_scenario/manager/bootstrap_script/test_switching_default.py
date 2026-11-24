"""자기 default bootstrap script 바꾸기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.bootstrap_script.request import (
    SwitchDefaultBootstrapScriptInput,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.response import BootstrapScriptNode
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
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
class SwitchingToMyExtraScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    """default 가 아닌 자기 script 를 default 로 지정한다."""

    @override
    def operation(self) -> str:
        return "switch_default"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 default 가 아닌 자기 bootstrap script 를 default 로 지정합니다",
            english=f"{laid.caller.username} sets their bootstrap script that is not the default as the default",
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> BootstrapScriptNode:
        with ActingAs(laid.caller):
            payload = await adapter.switch_default(
                SwitchDefaultBootstrapScriptInput(
                    user_id=UserID(laid.caller.id), id=laid.extra.script_id
                )
            )
        return payload.bootstrap_script


@dataclass(frozen=True)
class AUserGrantedUpdateSwitchesTheirDefault(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-switches-their-default-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 default 로 지정하면, 그 script 가 응답으로 옵니다",
            english="when a user granted UPDATE on their own user sets their bootstrap script that is not the default as the default, that script comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]:
        return SwitchingToMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptNode]:
        return TheBootstrapScriptNode(started=self.started, default=False)


@dataclass(frozen=True)
class AUserGrantedReadMayNotSwitchTheirDefault(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-switch-their-default-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 default 로 지정하려 하면 권한 부족으로 거부됩니다",
            english="when a user granted only READ on their own user tries to set their bootstrap script as the default, it is rejected for lack of permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode]:
        return SwitchingToMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptNode]:
        return TheCallIsRefused(NotEnoughPermission)


type Step = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptNode
]

SCENARIOS: list[Step] = [
    AUserGrantedUpdateSwitchesTheirDefault(started=datetime.now(UTC)),
    AUserGrantedReadMayNotSwitchTheirDefault(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_switching_default(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
