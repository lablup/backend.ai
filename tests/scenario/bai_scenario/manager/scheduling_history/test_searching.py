"""이력 전체 훑기 — 슈퍼관리자만 부를 수 있고, 미리 만든 이력 하나가 한 페이지로 온다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchKernelHistoriesInput,
    AdminSearchReplicaGroupHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
)
from ai.backend.manager.api.adapters.scheduling_history.adapter import (
    SchedulingHistoryAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.scheduling_history import (
    DEPLOYMENT,
    KERNEL,
    REPLICA_GROUP,
    ROUTE,
    SESSION,
    HistoriesAndACaller,
    HistoriesAndSomeone,
    Side,
    TheHistoriesAreFound,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, Any]

LABELS: dict[str, tuple[str, str]] = {
    SESSION: ("세션", "session"),
    KERNEL: ("커널", "kernel"),
    DEPLOYMENT: ("배포", "deployment"),
    ROUTE: ("라우트", "route"),
    REPLICA_GROUP: ("복제본 그룹", "replica group"),
}


@dataclass(frozen=True)
class SearchingTheHistories(When[HistoriesAndACaller, SchedulingHistoryAdapter, Any]):
    """``kind`` 의 이력을 필터 없이 훑는다."""

    kind: str

    @override
    def operation(self) -> str:
        return f"admin_search_{self.kind}_history"

    @override
    def describe(self, laid: HistoriesAndACaller) -> str:
        where, where_en = LABELS[self.kind]
        return Says(
            f"{laid.caller.username} 이 필터 없이 {where} 이력을 훑습니다",
            english=f"{laid.caller.username} pages through every {where_en} history without a filter",
        )

    @override
    async def call(self, adapter: SchedulingHistoryAdapter, laid: HistoriesAndACaller) -> Any:
        with ActingAs(laid.caller):
            match self.kind:
                case "session":
                    return await adapter.admin_search_session_history(
                        AdminSearchSessionHistoriesInput()
                    )
                case "kernel":
                    return await adapter.admin_search_kernel_history(
                        AdminSearchKernelHistoriesInput()
                    )
                case "deployment":
                    return await adapter.admin_search_deployment_history(
                        AdminSearchDeploymentHistoriesInput()
                    )
                case "route":
                    return await adapter.admin_search_route_history(
                        AdminSearchRouteHistoriesInput()
                    )
                case _:
                    return await adapter.admin_search_replica_group_history(
                        AdminSearchReplicaGroupHistoriesInput()
                    )


@dataclass(frozen=True)
class SearchRow(Scenario[TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, Any]):
    named: str
    guarantees: str
    kind: str
    who: Side = Side.SUPERADMIN
    refused: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, HistoriesAndACaller]:
        return HistoriesAndSomeone(who=self.who)

    @override
    def when(self) -> When[HistoriesAndACaller, SchedulingHistoryAdapter, Any]:
        return SearchingTheHistories(kind=self.kind)

    @override
    def then(self) -> Then[HistoriesAndACaller, Any]:
        if self.refused:
            return TheCallIsRefused(InsufficientPrivilege)
        return TheHistoriesAreFound(kind=self.kind, started=STARTED)


STARTED = datetime.now(UTC)


def _row(kind: str, *, refused: bool = False) -> SearchRow:
    where, where_en = LABELS[kind]
    slug = kind.replace("_", "-")
    if refused:
        return SearchRow(
            named=f"a-user-granted-nothing-may-not-page-through-{slug}-histories",
            guarantees=Says(
                f"슈퍼관리자가 아닌 사용자가 {where} 이력을 훑으면 권한 부족으로 거부됩니다",
                english=(
                    "when a user other than the superadmin pages through "
                    f"{where_en} histories, the call is rejected for lack of privilege"
                ),
            ),
            kind=kind,
            who=Side.NOBODY,
            refused=True,
        )
    return SearchRow(
        named=f"the-superadmin-pages-through-{slug}-histories",
        guarantees=Says(
            f"슈퍼관리자가 {where} 이력을 훑으면 미리 만든 이력 하나가 한 페이지로 옵니다",
            english=(
                f"when the superadmin pages through {where_en} histories, the one history laid "
                "in advance comes back as one page"
            ),
        ),
        kind=kind,
    )


SCENARIOS: list[SearchStep] = [
    _row(SESSION),
    _row(SESSION, refused=True),
    _row(KERNEL),
    _row(KERNEL, refused=True),
    _row(DEPLOYMENT),
    _row(DEPLOYMENT, refused=True),
    _row(ROUTE),
    _row(ROUTE, refused=True),
    _row(REPLICA_GROUP),
    _row(REPLICA_GROUP, refused=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: SchedulingHistoryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
