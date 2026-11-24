"""자기 사용자에 bootstrap script 추가하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.bootstrap_script.request import CreateBootstrapScriptInput
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

type CreatingStep = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode
]


@dataclass(frozen=True)
class AddingMyScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]
):
    """자기 사용자에 새 bootstrap script 를 추가한다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 사용자에 내용이 {NEW_SCRIPT!r} 인 bootstrap script 를 추가합니다",
            english=(
                f"{laid.caller.username} adds a bootstrap script holding {NEW_SCRIPT!r} to their own user"
            ),
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> BootstrapScriptRevisionNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateBootstrapScriptInput(user_id=UserID(laid.caller.id), script=NEW_SCRIPT)
            )
        return payload.revision


@dataclass(frozen=True)
class AUserGrantedUpdateAddsAScript(
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
        return "a-user-granted-update-adds-a-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 권한을 받은 사용자가 bootstrap script 를 추가하면, 새 script 의 "
            "revision 1 이 응답으로 옵니다",
            english=(
                "when a user granted UPDATE on their own user adds a bootstrap script, revision 1 "
                "of the new script comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]:
        return AddingMyScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptRevisionNode]:
        return TheRevisionNode(started=self.started, revision_number=1, on_extra=False)


@dataclass(frozen=True)
class AUserGrantedReadMayNotAddAScript(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        BootstrapScriptRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-add-a-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 bootstrap script 를 추가하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted only READ on their own user tries to add a bootstrap script, "
                "it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, BootstrapScriptRevisionNode]:
        return AddingMyScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, BootstrapScriptRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CreatingStep] = [
    AUserGrantedUpdateAddsAScript(started=datetime.now(UTC)),
    AUserGrantedReadMayNotAddAScript(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
