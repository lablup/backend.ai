"""bootstrap script 를 id 로 한 번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.bootstrap_script.response import BootstrapScriptNode
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.bootstrap_script import (
    BootstrapScriptHolder,
    SomeoneWithBootstrapScripts,
    script_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[BootstrapScriptNode | Exception | None]
type Step = Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, Answer]


@dataclass(frozen=True)
class LoadingMyDefaultScript(When[BootstrapScriptHolder, BootstrapScriptAdapter, Answer]):
    """자기 default script 의 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 default bootstrap script 를 id 로 일괄 조회합니다",
            english=f"{laid.caller.username} loads their default bootstrap script by id in one call",
        )

    @override
    async def call(self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([laid.default.script_id])


@dataclass(frozen=True)
class LoadingMineAndAStrangers(When[BootstrapScriptHolder, BootstrapScriptAdapter, Answer]):
    """자기 default script 와 다른 사용자의 script 를 함께 준다."""

    @override
    def operation(self) -> str:
        return "bulk_get_ids"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 default bootstrap script 와 다른 사용자의 bootstrap "
            "script 를 id 로 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads their default bootstrap script and the bootstrap "
                "script of another user by id in one call"
            ),
        )

    @override
    async def call(self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_ids([
                laid.default.script_id,
                laid.stranger_script().script_id,
            ])


@dataclass(frozen=True)
class MyScriptAlone(Then[BootstrapScriptHolder, Answer]):
    """자기 default script 하나가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자기 default script 하나가 응답으로 옵니다",
            english="their one default script comes back",
        )

    @override
    def look(self, laid: BootstrapScriptHolder, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Same("raised", answered.raised, None)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, BootstrapScriptNode):
            seen.extend(script_verdicts("[0].", first, laid, self.started, True))
        else:
            seen.append(Same("[0]", type(first).__name__, "BootstrapScriptNode"))
        return seen


@dataclass(frozen=True)
class MineAndARefusal(Then[BootstrapScriptHolder, Answer]):
    """자기 script 는 오고, 다른 사용자의 script 자리는 권한 부족으로 거부된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자기 script 는 오고, 다른 사용자의 script 자리는 권한 부족으로 거부됩니다",
            english=(
                "their own script comes back, and the entry of the other user's script is "
                "rejected for lack of permission"
            ),
        )

    @override
    def look(self, laid: BootstrapScriptHolder, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Same("raised", answered.raised, None)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        first = loaded[0] if loaded else None
        if isinstance(first, BootstrapScriptNode):
            seen.extend(script_verdicts("[0].", first, laid, self.started, True))
        else:
            seen.append(Same("[0]", type(first).__name__, "BootstrapScriptNode"))
        second = loaded[1] if len(loaded) > 1 else None
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        return seen


@dataclass(frozen=True)
class AUserGrantedReadLoadsTheirScript(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-their-bootstrap-script-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 를 id 로 일괄 조회하면, "
            "그 script 가 응답으로 옵니다",
            english=(
                "when a user granted READ on their own user loads their bootstrap script by id, "
                "that script comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,))

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, Answer]:
        return LoadingMyDefaultScript()

    @override
    def then(self) -> Then[BootstrapScriptHolder, Answer]:
        return MyScriptAlone(started=self.started)


@dataclass(frozen=True)
class AStrangersScriptIsRefusedInTheBatch(
    Scenario[TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-strangers-bootstrap-script-is-rejected-in-the-batch"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 script 와 다른 사용자의 script 를 id 로 "
            "일괄 조회하면, 호출은 성공하되 다른 사용자의 script 자리는 권한 부족으로 거부됩니다",
            english=(
                "when a user granted READ on their own user loads their script and another "
                "user's script by id, the call succeeds but the entry of the other user's script "
                "is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,), stranger=True)

    @override
    def when(self) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, Answer]:
        return LoadingMineAndAStrangers()

    @override
    def then(self) -> Then[BootstrapScriptHolder, Answer]:
        return MineAndARefusal(started=self.started)


SCENARIOS: list[Step] = [
    AUserGrantedReadLoadsTheirScript(started=datetime.now(UTC)),
    AStrangersScriptIsRefusedInTheBatch(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
