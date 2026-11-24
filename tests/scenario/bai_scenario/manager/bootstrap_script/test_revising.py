"""default 가 아닌 자기 bootstrap script 의 내용 바꾸기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.bootstrap_script.request import (
    AddBootstrapScriptRevisionInput,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.response import BootstrapScriptRevisionNode
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.bootstrap_script import (
    NEW_SCRIPT,
    BootstrapScriptHolder,
    SomeoneWithBootstrapScripts,
    TheRevisionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class RevisingMyExtraScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]
):
    """default 가 아닌 자기 script 에 revision 을 더한다."""

    @override
    def operation(self) -> str:
        return "add_revision"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 default 가 아닌 자기 bootstrap script 의 내용을 {NEW_SCRIPT!r} 로 바꿉니다",
            english=f"{laid.caller.username} replaces the content of their bootstrap script that is not the default with {NEW_SCRIPT!r}",
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> BootstrapScriptRevisionNode:
        with ActingAs(laid.caller):
            payload = await adapter.add_revision(
                AddBootstrapScriptRevisionInput(id=laid.extra.script_id, script=NEW_SCRIPT),
                UserID(laid.caller.id),
            )
        return payload.revision


@dataclass(frozen=True)
class AUserGrantedUpdateRevisesTheirScript(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        BootstrapScriptRevisionNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-adds-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ, UPDATE 권한을 받은 사용자가 자기 bootstrap script 의 내용을 바꾸면, revision 2 가 응답으로 옵니다",
            english="when a user granted READ and UPDATE on their own user replaces the content of their bootstrap script, revision 2 comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]:
        return RevisingMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptRevisionNode]:
        return TheRevisionNode(started=self.started, revision_number=2, on_extra=True)


@dataclass(frozen=True)
class AUserGrantedReadMayNotReviseTheirScript(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        BootstrapScriptRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-add-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 의 내용을 바꾸려 하면 권한 부족으로 거부됩니다",
            english="when a user granted only READ on their own user tries to replace the content of their bootstrap script, it is rejected for lack of permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]:
        return RevisingMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


type Step = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode
]

SCENARIOS: list[Step] = [
    AUserGrantedUpdateRevisesTheirScript(started=datetime.now(UTC)),
    AUserGrantedReadMayNotReviseTheirScript(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_revising(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
