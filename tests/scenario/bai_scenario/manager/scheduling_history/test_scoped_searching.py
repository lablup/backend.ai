"""범위를 대고 이력 훑기 — 세션, 커널, 배포, 라우트, 복제본 그룹."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
    ScopedSearchKernelHistoriesInput,
    ScopedSearchReplicaGroupHistoriesInput,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    KernelHistoryScopeDTO,
    ReplicaGroupHistoryScopeDTO,
)
from ai.backend.manager.api.adapters.scheduling_history.adapter import (
    SchedulingHistoryAdapter,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
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

type ScopedStep = Scenario[
    TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, Any
]

LABELS: dict[str, tuple[str, str]] = {
    SESSION: ("세션", "session"),
    KERNEL: ("커널", "kernel"),
    DEPLOYMENT: ("배포", "deployment"),
    ROUTE: ("라우트", "route"),
    REPLICA_GROUP: ("복제본 그룹", "replica group"),
}


@dataclass(frozen=True)
class SearchingWithinTheScope(
    When[HistoriesAndACaller, SchedulingHistoryAdapter, Any]
):
    """``kind`` 가 가리키는 대상을 범위로 그 이력을 훑는다."""

    kind: str
    two_items: bool = False

    @override
    def operation(self) -> str:
        match self.kind:
            case "session":
                return "session_scoped_search"
            case "kernel":
                return "scoped_search_kernel_history"
            case "deployment":
                return "deployment_scoped_search"
            case "route":
                return "route_scoped_search"
            case _:
                return "scoped_search_replica_group_history"

    @override
    def describe(self, laid: HistoriesAndACaller) -> str:
        where, where_en = LABELS[self.kind]
        if self.two_items:
            return Says(
                f"{laid.caller.username} 이 범위 항목 둘을 대고 {where} 이력을 훑습니다",
                english=(
                    f"{laid.caller.username} pages through {where_en} histories naming two "
                    "scope items"
                ),
            )
        return Says(
            f"{laid.caller.username} 이 미리 만든 대상 하나를 범위로 {where} 이력을 훑습니다",
            english=(
                f"{laid.caller.username} pages through {where_en} histories naming the target "
                "laid in advance as the scope"
            ),
        )

    @override
    async def call(self, adapter: SchedulingHistoryAdapter, laid: HistoriesAndACaller) -> Any:
        with ActingAs(laid.caller):
            match self.kind:
                case "session":
                    return await adapter.session_scoped_search(
                        UUID(str(laid.session.id)), AdminSearchSessionHistoriesInput()
                    )
                case "kernel":
                    sessions = [UUIDScope(value=UUID(str(laid.session.id)))]
                    if self.two_items:
                        sessions.append(UUIDScope(value=UUID(int=9)))
                    return await adapter.scoped_search_kernel_history(
                        ScopedSearchKernelHistoriesInput(
                            scope=KernelHistoryScopeDTO(session=sessions)
                        )
                    )
                case "deployment":
                    return await adapter.deployment_scoped_search(
                        UUID(str(laid.deployment.id)),
                        AdminSearchDeploymentHistoriesInput(),
                    )
                case "route":
                    return await adapter.route_scoped_search(
                        UUID(str(laid.replica.id)), AdminSearchRouteHistoriesInput()
                    )
                case _:
                    deployments = [UUIDScope(value=UUID(str(laid.deployment.id)))]
                    if self.two_items:
                        deployments.append(UUIDScope(value=UUID(int=9)))
                    return await adapter.scoped_search_replica_group_history(
                        ScopedSearchReplicaGroupHistoriesInput(
                            scope=ReplicaGroupHistoryScopeDTO(deployment=deployments)
                        )
                    )


@dataclass(frozen=True)
class ScopedRow(
    Scenario[TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, Any]
):
    named: str
    guarantees: str
    kind: str
    who: Side = Side.SUPERADMIN
    two_items: bool = False
    expected: type[BaseException] | None = None

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
        return SearchingWithinTheScope(kind=self.kind, two_items=self.two_items)

    @override
    def then(self) -> Then[HistoriesAndACaller, Any]:
        if self.expected is not None:
            return TheCallIsRefused(self.expected)
        return TheHistoriesAreFound(kind=self.kind, started=STARTED)


STARTED = datetime.now(UTC)


def _row(kind: str, *, refused: bool = False, two_items: bool = False) -> ScopedRow:
    where, where_en = LABELS[kind]
    slug = kind.replace("_", "-")
    if refused:
        # A replica names its deployment through a lookup that answers a denial and an
        # unknown id alike, so a route scope is refused with the generic bad request.
        expected = GenericBadRequest if kind == ROUTE else NotEnoughPermission
        if kind == ROUTE:
            guarantees = Says(
                "아무 권한도 받지 않은 사용자가 라우트 이력을 범위로 훑으면 요청이 거부됩니다",
                english=(
                    "when a user granted nothing pages through the route histories of a scope, "
                    "the request is rejected"
                ),
            )
        else:
            guarantees = Says(
                f"아무 권한도 받지 않은 사용자가 {where} 이력을 범위로 훑으면 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing pages through "
                    f"{where_en} histories of a scope, the call is rejected for lack of permission"
                ),
            )
        return ScopedRow(
            named=f"a-user-granted-nothing-may-not-page-through-the-scoped-{slug}-histories",
            guarantees=guarantees,
            kind=kind,
            who=Side.NOBODY,
            expected=expected,
        )
    if two_items:
        return ScopedRow(
            named=f"{slug}-history-scope-naming-two-items-is-refused",
            guarantees=Says(
                f"슈퍼관리자가 범위 항목 둘을 대고 {where} 이력을 훑으면 요청이 거부됩니다",
                english=(
                    "when the superadmin pages through "
                    f"{where_en} histories naming two scope items, the request is rejected"
                ),
            ),
            kind=kind,
            two_items=True,
            expected=InvalidAPIParameters,
        )
    return ScopedRow(
        named=f"the-superadmin-pages-through-the-scoped-{slug}-histories",
        guarantees=Says(
            f"슈퍼관리자가 미리 만든 대상을 범위로 {where} 이력을 훑으면 그 이력 하나가 한 "
            "페이지로 옵니다",
            english=(
                f"when the superadmin pages through {where_en} histories of the target laid in "
                "advance, the one history comes back as one page"
            ),
        ),
        kind=kind,
    )


SCENARIOS: list[ScopedStep] = [
    _row(SESSION),
    _row(SESSION, refused=True),
    _row(KERNEL),
    _row(KERNEL, refused=True),
    _row(KERNEL, two_items=True),
    _row(DEPLOYMENT),
    _row(DEPLOYMENT, refused=True),
    _row(ROUTE),
    _row(ROUTE, refused=True),
    _row(REPLICA_GROUP),
    _row(REPLICA_GROUP, refused=True),
    _row(REPLICA_GROUP, two_items=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: ScopedStep, adapter: SchedulingHistoryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
