"""이력 여러 줄을 id 로 한 번에 읽기 — 있으면 노드, 없으면 빈 값, 남의 것이면 거부."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.manager.api.adapters.scheduling_history.adapter import (
    SchedulingHistoryAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.scheduling_history import (
    DEPLOYMENT,
    KERNEL,
    REPLICA_GROUP,
    ROUTE,
    SESSION,
    HistoriesAndACaller,
    HistoriesAndSomeone,
    Side,
    TheHistoryComesBack,
    TheHistoryLoadIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN = UUID(int=9)
"""어느 표에도 없는 id."""

type LoadStep = Scenario[
    TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, list[Any]
]

LABELS: dict[str, tuple[str, str]] = {
    SESSION: ("세션", "session"),
    KERNEL: ("커널", "kernel"),
    DEPLOYMENT: ("배포", "deployment"),
    ROUTE: ("라우트", "route"),
    REPLICA_GROUP: ("복제본 그룹", "replica group"),
}


def _ids(kind: str, ids: list[UUID]) -> list[Any]:
    match kind:
        case "session":
            return [SessionSchedulingHistoryID(one) for one in ids]
        case "kernel":
            return [KernelSchedulingHistoryID(one) for one in ids]
        case "deployment":
            return [DeploymentHistoryID(one) for one in ids]
        case "route":
            return [RouteHistoryID(one) for one in ids]
        case _:
            return [ReplicaGroupHistoryID(one) for one in ids]


@dataclass(frozen=True)
class LoadingTheHistories(When[HistoriesAndACaller, SchedulingHistoryAdapter, list[Any]]):
    """``kind`` 의 이력을 id 로 읽는다. ``missing`` 이면 없는 id 를 뒤에 하나 더 붙인다."""

    kind: str
    missing: bool = False

    @override
    def operation(self) -> str:
        return f"batch_load_{self.kind}_histories_by_ids"

    @override
    def describe(self, laid: HistoriesAndACaller) -> str:
        where = LABELS[self.kind][0]
        where_en = LABELS[self.kind][1]
        ids = "미리 만든 id" if not self.missing else "미리 만든 id 와 없는 id"
        ids_en = (
            "the id laid in advance"
            if not self.missing
            else "the id laid in advance and an unknown id"
        )
        return Says(
            f"{laid.caller.username} 이 {ids} 로 {where} 이력을 읽습니다",
            english=f"{laid.caller.username} reads the {where_en} histories by {ids_en}",
        )

    @override
    async def call(self, adapter: SchedulingHistoryAdapter, laid: HistoriesAndACaller) -> list[Any]:
        ids = [laid.history_id(self.kind)]
        if self.missing:
            ids.append(UNKNOWN)
        with ActingAs(laid.caller):
            match self.kind:
                case "session":
                    return await adapter.batch_load_session_histories_by_ids(_ids(self.kind, ids))
                case "kernel":
                    return await adapter.batch_load_kernel_histories_by_ids(_ids(self.kind, ids))
                case "deployment":
                    return await adapter.batch_load_deployment_histories_by_ids(
                        _ids(self.kind, ids)
                    )
                case "route":
                    return await adapter.batch_load_route_histories_by_ids(_ids(self.kind, ids))
                case _:
                    return await adapter.batch_load_replica_group_histories_by_ids(
                        _ids(self.kind, ids)
                    )


@dataclass(frozen=True)
class LoadRow(
    Scenario[TestSeedingSession, HistoriesAndACaller, SchedulingHistoryAdapter, list[Any]]
):
    named: str
    guarantees: str
    kind: str
    who: Side = Side.SUPERADMIN
    missing: bool = False
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
    def when(self) -> When[HistoriesAndACaller, SchedulingHistoryAdapter, list[Any]]:
        return LoadingTheHistories(kind=self.kind, missing=self.missing)

    @override
    def then(self) -> Then[HistoriesAndACaller, list[Any]]:
        if self.refused:
            return TheHistoryLoadIsRefused()
        return TheHistoryComesBack(kind=self.kind, started=STARTED, missing=self.missing)


STARTED = datetime.now(UTC)


def _row(kind: str, *, missing: bool = False, refused: bool = False) -> LoadRow:
    where, where_en = LABELS[kind]
    if refused:
        return LoadRow(
            named=f"a-user-granted-nothing-may-not-load-the-{kind.replace('_', '-')}-history",
            guarantees=Says(
                f"아무 권한도 받지 않은 사용자가 남의 {where} 이력을 id 로 읽으면 그 자리가 "
                "권한 부족으로 거부됩니다",
                english=(
                    "when a user granted nothing reads another's "
                    f"{where_en} history by id, that entry is rejected for lack of permission"
                ),
            ),
            kind=kind,
            who=Side.NOBODY,
            refused=True,
        )
    if missing:
        return LoadRow(
            named=(f"the-superadmin-loads-the-{kind.replace('_', '-')}-history-with-an-unknown-id"),
            guarantees=Says(
                f"슈퍼관리자가 있는 id 와 없는 id 로 {where} 이력을 읽으면, 있는 것은 노드로 "
                "오고 없는 자리는 빈 값입니다",
                english=(
                    "when the superadmin reads "
                    f"{where_en} histories by a known and an unknown id, the known one comes "
                    "back as a node and the unknown entry as an empty value"
                ),
            ),
            kind=kind,
            missing=True,
        )
    return LoadRow(
        named=f"the-superadmin-loads-the-{kind.replace('_', '-')}-history",
        guarantees=Says(
            f"슈퍼관리자가 {where} 이력을 id 로 읽으면 그 이력이 노드로 통째로 옵니다",
            english=(
                f"when the superadmin reads a {where_en} history by its id, the history comes "
                "back whole as a node"
            ),
        ),
        kind=kind,
    )


SCENARIOS: list[LoadStep] = [
    _row(SESSION),
    _row(SESSION, missing=True),
    _row(SESSION, refused=True),
    _row(KERNEL),
    _row(KERNEL, missing=True),
    _row(KERNEL, refused=True),
    _row(DEPLOYMENT),
    _row(DEPLOYMENT, missing=True),
    _row(DEPLOYMENT, refused=True),
    _row(ROUTE),
    _row(ROUTE, missing=True),
    _row(ROUTE, refused=True),
    _row(REPLICA_GROUP),
    _row(REPLICA_GROUP, missing=True),
    _row(REPLICA_GROUP, refused=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: SchedulingHistoryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
