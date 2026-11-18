"""여러 id로 조회 — 기록 소유자의 READ 권한을 항목마다 검사하고, 항목마다 따로 응답한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.login_history import (
    HistoryToLoad,
    HistoryToRead,
    Loaded,
    TheSlotsInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type LoadingStep = Scenario[TestSeedingSession, HistoryToLoad, LoginHistoryAdapter, Loaded]


@dataclass(frozen=True)
class LoadingByIds(When[HistoryToLoad, LoginHistoryAdapter, Loaded]):
    """이름으로 고른 기록들을 id 로 한 번에 조회한다."""

    names: tuple[str, ...]

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: HistoryToLoad) -> str:
        return Says(
            f"{laid.caller.username}이 기록 {len(self.names)}개를 id 로 한 번에 조회합니다",
            english=f"{laid.caller.username} reads {len(self.names)} records by id at once",
        )

    @override
    async def call(self, adapter: LoginHistoryAdapter, laid: HistoryToLoad) -> Loaded:
        records = {"mine": laid.mine, "also_mine": laid.also_mine, "theirs": laid.theirs}
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                LoginHistoryID(records[name].id) for name in self.names
            ])


@dataclass(frozen=True)
class AGrantedUserLoadsTheirOwnRecords(
    Scenario[TestSeedingSession, HistoryToLoad, LoginHistoryAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-loads-their-own-records-in-order"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 자기 기록 둘을 id 로 조회하면, 요청한 순서대로 "
            "노드 전체가 반환됩니다",
            english=(
                "when a user granted READ on themselves reads two of their own records by "
                "id, whole nodes come back in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToLoad]:
        return HistoryToRead()

    @override
    def when(self) -> When[HistoryToLoad, LoginHistoryAdapter, Loaded]:
        return LoadingByIds(("also_mine", "mine"))

    @override
    def then(self) -> Then[HistoryToLoad, Loaded]:
        return TheSlotsInOrder(("also_mine", "mine"), self.started)


@dataclass(frozen=True)
class ARecordOfAnotherUserIsRefusedInItsSlot(
    Scenario[TestSeedingSession, HistoryToLoad, LoginHistoryAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-record-of-another-user-is-refused-in-its-own-slot"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 자기 기록과 다른 사용자의 기록을 함께 조회하면, "
            "자기 기록은 노드 전체로, 다른 사용자의 기록은 권한 부족으로 그 항목에만 응답합니다",
            english=(
                "when a user granted READ on themselves reads a record of their own and a "
                "record of another user, their own comes back as a whole node and only the "
                "other user's item answers with a permission failure"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, HistoryToLoad]:
        return HistoryToRead()

    @override
    def when(self) -> When[HistoryToLoad, LoginHistoryAdapter, Loaded]:
        return LoadingByIds(("mine", "theirs"))

    @override
    def then(self) -> Then[HistoryToLoad, Loaded]:
        return TheSlotsInOrder(("mine", "refused"), self.started)


SCENARIOS: list[LoadingStep] = [
    AGrantedUserLoadsTheirOwnRecords(started=datetime.now(UTC)),
    ARecordOfAnotherUserIsRefusedInItsSlot(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: LoginHistoryAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
