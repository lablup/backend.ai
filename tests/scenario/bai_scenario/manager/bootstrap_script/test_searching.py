"""한 사용자의 bootstrap script 검색하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.bootstrap_script.request import (
    BootstrapScriptFilter,
    BootstrapScriptOrder,
    ScopedSearchBootstrapScriptsInput,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.response import (
    SearchBootstrapScriptsPayload,
)
from ai.backend.common.dto.manager.v2.bootstrap_script.types import (
    BootstrapScriptOrderField,
    BootstrapScriptScope,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.bootstrap_script.adapter import BootstrapScriptAdapter
from ai.backend.manager.data.permission.types import Permission
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.bootstrap_script import (
    BootstrapScriptHolder,
    SomeoneWithBootstrapScripts,
    script_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Step = Scenario[
    TestSeedingSession, BootstrapScriptHolder, BootstrapScriptAdapter, SearchBootstrapScriptsPayload
]


@dataclass(frozen=True)
class SearchingMyScriptsNotDefault(
    When[BootstrapScriptHolder, BootstrapScriptAdapter, SearchBootstrapScriptsPayload]
):
    """자기 script 중 default 가 아닌 것만, 만든 시각이 늦은 순으로, 10개까지 찾는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: BootstrapScriptHolder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 bootstrap script 중 default 가 아닌 것을 만든 시각이 늦은 "
            "순으로 10개까지 검색합니다",
            english=(
                f"{laid.caller.username} searches their bootstrap scripts that are not the default, "
                "latest created first, up to 10"
            ),
        )

    @override
    async def call(
        self, adapter: BootstrapScriptAdapter, laid: BootstrapScriptHolder
    ) -> SearchBootstrapScriptsPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchBootstrapScriptsInput(
                    scope=BootstrapScriptScope(user=[UUIDScope(value=laid.caller.id)]),
                    filter=BootstrapScriptFilter(is_default=False),
                    order=[
                        BootstrapScriptOrder(
                            field=BootstrapScriptOrderField.CREATED_AT,
                            direction=OrderDirection.DESC,
                        )
                    ],
                    limit=10,
                    offset=0,
                )
            )


@dataclass(frozen=True)
class OnlyTheExtraScript(Then[BootstrapScriptHolder, SearchBootstrapScriptsPayload]):
    """default 가 아닌 자기 script 하나만 온다. default script 와 다른 사용자의 script 는 오지 않는다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "default 가 아닌 자기 script 하나만 응답으로 옵니다",
            english="only their one script that is not the default comes back",
        )

    @override
    def look(
        self, laid: BootstrapScriptHolder, answered: Answered[SearchBootstrapScriptsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Same("raised", answered.raised, None)]
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("len(items)", len(page.items), 1),
        ]
        if page.items:
            seen.extend(script_verdicts("items[0].", page.items[0], laid, self.started, False))
        return seen


@dataclass(frozen=True)
class AUserGrantedReadSearchesTheirScripts(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        SearchBootstrapScriptsPayload,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-searches-their-bootstrap-scripts"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 bootstrap script 중 default 가 아닌 것을 "
            "검색하면, 그 script 만 오고 default script 와 다른 사용자의 script 는 오지 않습니다",
            english=(
                "when a user granted READ on their own user searches their bootstrap scripts that "
                "are not the default, only that script comes back, not the default one nor the "
                "script of another user"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts(permissions=(Permission.READ,), stranger=True)

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, SearchBootstrapScriptsPayload]:
        return SearchingMyScriptsNotDefault()

    @override
    def then(self) -> Then[BootstrapScriptHolder, SearchBootstrapScriptsPayload]:
        return OnlyTheExtraScript(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirScripts(
    Scenario[
        TestSeedingSession,
        BootstrapScriptHolder,
        BootstrapScriptAdapter,
        SearchBootstrapScriptsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-bootstrap-scripts"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 bootstrap script 를 검색하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to search their bootstrap scripts, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, BootstrapScriptHolder]:
        return SomeoneWithBootstrapScripts()

    @override
    def when(
        self,
    ) -> When[BootstrapScriptHolder, BootstrapScriptAdapter, SearchBootstrapScriptsPayload]:
        return SearchingMyScriptsNotDefault()

    @override
    def then(self) -> Then[BootstrapScriptHolder, SearchBootstrapScriptsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[Step] = [
    AUserGrantedReadSearchesTheirScripts(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirScripts(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: Step, adapter: BootstrapScriptAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
