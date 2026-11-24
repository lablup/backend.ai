"""자기 bootstrap script 지우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.bootstrap_script.request import PurgeBootstrapScriptInput
from ai.backend.common.dto.manager.v2.bootstrap_script.response import PurgeBootstrapScriptPayload
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.bootstrap_script import DefaultBootstrapScriptPurgeForbidden
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.bootstrap_script import (
    BootstrapScriptHolder,
    SomeoneWithBootstrapScripts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class PurgingMyExtraScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload]
):
    """default 가 아닌 자기 script 를 지운다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 default 가 아닌 자기 bootstrap script 를 지웁니다",
            english=f"{laid.caller.username} purges their bootstrap script that is not the default",
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> PurgeBootstrapScriptPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(PurgeBootstrapScriptInput(id=laid.extra.script_id))


@dataclass(frozen=True)
class PurgingMyDefaultScript(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload]
):
    """자기 default script 를 지운다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 default bootstrap script 를 지웁니다",
            english=f"{laid.caller.username} purges their default bootstrap script",
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> PurgeBootstrapScriptPayload:
        with ActingAs(laid.caller):
            return await adapter.purge(PurgeBootstrapScriptInput(id=laid.default.script_id))


@dataclass(frozen=True)
class TheExtraScriptIsGone(Then[BootstrapScriptHolder, PurgeBootstrapScriptPayload]):
    """지운 script 의 id 가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "지운 script 의 id 가 응답으로 옵니다", english="the id of the purged script comes back"
        )

    @override
    def look(
        self, laid: BootstrapScriptHolder, answered: Answered[PurgeBootstrapScriptPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        return [
            Held[UUID](
                "field_id",
                payload.field_id,
                SameAs(
                    laid.extra.script_id,
                    Says(
                        "심어 둔 default 가 아닌 script",
                        english="the seeded script that is not the default",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class AUserGrantedUpdatePurgesTheirScript(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        PurgeBootstrapScriptPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-purges-their-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 bootstrap script 를 지우면, 지운 script 의 id 가 응답으로 옵니다",
            english="when a user granted READ and UPDATE on their own user purges their bootstrap script that is not the default, the id of that script comes back",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload]:
        return PurgingMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, PurgeBootstrapScriptPayload]:
        return TheExtraScriptIsGone()


@dataclass(frozen=True)
class AUserGrantedReadMayNotPurgeTheirScript(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        PurgeBootstrapScriptPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-purge-their-bootstrap-script"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 자기 bootstrap script 를 지우려 하면 권한 부족으로 거부됩니다",
            english="when a user granted only READ on their own user tries to purge their bootstrap script, it is rejected for lack of permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload]:
        return PurgingMyExtraScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, PurgeBootstrapScriptPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheDefaultScriptIsNotPurged(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        PurgeBootstrapScriptPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-default-bootstrap-script-is-not-purged"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ, UPDATE 권한을 받은 사용자라도 자기 default bootstrap script 를 지우려 하면, default 를 먼저 바꾸라며 거부됩니다",
            english="when a user granted READ and UPDATE on their own user tries to purge their default bootstrap script, it is rejected until the default moves",
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload]:
        return PurgingMyDefaultScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, PurgeBootstrapScriptPayload]:
        return TheCallIsRefused(DefaultBootstrapScriptPurgeForbidden)


type Step = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, PurgeBootstrapScriptPayload
]

SCENARIOS: list[Step] = [
    AUserGrantedUpdatePurgesTheirScript(),
    AUserGrantedReadMayNotPurgeTheirScript(),
    TheDefaultScriptIsNotPurged(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
