"""여러 폴더를 한 요청에 지우기 — 하나가 막혀도 나머지는 간다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
from bai_scenario.components.vfolder.answers import (
    NoAnswer,
)
from bai_scenario.components.vfolder.callers import (
    FoldersTheCallerMayAndMayNotDelete,
    TheirFoldersToDelete,
)
from bai_scenario.components.vfolder.stage import (
    FoldersAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.vfolder.request import BulkDeleteVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkDeleteVFoldersPayload,
    DeleteVFolderPayload,
    RestoreVFolderPayload,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

type Answer = DeleteVFolderPayload | RestoreVFolderPayload | BulkDeleteVFoldersPayload
type RetiringStep = Scenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class SendingThemAllToTheTrash(When[FoldersAndACaller, VFolderAdapter, Answer]):
    """서 있는 폴더들을 한 요청에 함께 지운다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: FoldersAndACaller) -> str:
        return f"{laid.caller.username}이 폴더 {len(laid.seen) + len(laid.unseen)}개를 함께 지움"

    @override
    async def call(self, adapter: VFolderAdapter, laid: FoldersAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_delete(
                BulkDeleteVFoldersInput(ids=[one.id for one in (*laid.seen, *laid.unseen)])
            )


@dataclass(frozen=True)
class TheBatchIsAnsweredPerId(Then[FoldersAndACaller, Any]):
    """지운 것과 막힌 것을 함께 답한다."""

    deleted: int
    failed: int

    @override
    def says(self) -> str:
        return f"{self.deleted}개는 지워지고 {self.failed}개는 막힌 것으로 담겨 온다"

    @override
    def look(self, laid: FoldersAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkDeleteVFoldersPayload):
            return [NoAnswer(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.metadata.name for one in payload.items),
                sorted(one.name for one in laid.seen),
            ),
            Same("deleted_count", payload.deleted_count, self.deleted),
            Same("failed", len(payload.failed), self.failed),
            Held(
                "failed[].vfolder_id",
                [one.vfolder_id for one in payload.failed],
                SameAs[list[UUID]]([one.id for one in laid.unseen], "권한이 닿지 않는 폴더"),
            )
            if self.failed
            else Skipped("failed[].vfolder_id", "막힌 것이 없다"),
            Skipped("failed[].message", "예외 메시지를 그대로 담아 바뀌어도 되는 값이다"),
        ]


@dataclass(frozen=True)
class TwoOfTheirOwnGoTogether(Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "two-folders-of-ones-own-are-deleted-in-one-request"

    @override
    def describe(self) -> str:
        return (
            "지우기 권한을 받은 사용자가 자기 폴더 둘을 한 요청에 함께 지우면, "
            "둘 다 지워지고 막힌 것은 하나도 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return TheirFoldersToDelete(own=2)

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, Answer]:
        return SendingThemAllToTheTrash()

    @override
    def then(self) -> Then[FoldersAndACaller, Answer]:
        return TheBatchIsAnsweredPerId(deleted=2, failed=0)


@dataclass(frozen=True)
class WhatIsBlockedIsAnsweredApart(
    Scenario[SeedingSession, FoldersAndACaller, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "what-the-caller-may-not-delete-comes-back-apart-from-what-they-did"

    @override
    def describe(self) -> str:
        return (
            "권한이 닿는 폴더와 닿지 않는 폴더를 한 요청에 함께 지우면, 닿는 것만 지워지고 "
            "나머지는 요청 전체를 깨뜨리지 않고 막힌 것으로 담겨 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, FoldersAndACaller]:
        return FoldersTheCallerMayAndMayNotDelete()

    @override
    def when(self) -> When[FoldersAndACaller, VFolderAdapter, Answer]:
        return SendingThemAllToTheTrash()

    @override
    def then(self) -> Then[FoldersAndACaller, Answer]:
        return TheBatchIsAnsweredPerId(deleted=1, failed=1)


SCENARIOS: list[RetiringStep] = [
    TwoOfTheirOwnGoTogether(),
    WhatIsBlockedIsAnsweredApart(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_retiring(
    scenario: RetiringStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
