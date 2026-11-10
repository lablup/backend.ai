"""공유 하나를 id 로 읽기 — 자리마다 노드, 거부, 빈 값이 온다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.dto.manager.v2.entity_share.response import EntityShareNode
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.entity_share import (
    ASharedFolderAndACaller,
    ASharedFolderAndSomeone,
    Side,
    TheShareEntryIsRefused,
    TheShareNode,
    TheSharesComeBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=9)
"""어떤 공유도 갖지 않은 id."""

type Read = EntityShareNode
type Loaded = list[EntityShareNode | Exception | None]
type ReadStep = Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Read]
type LoadStep = Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Loaded]


@dataclass(frozen=True)
class ReadingTheShare(When[ASharedFolderAndACaller, EntityShareAdapter, Read]):
    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 폴더 {laid.folder.name}에 걸린 공유를 조회합니다",
            english=f"{laid.caller.username} reads the share of folder {laid.folder.name}",
        )

    @override
    async def call(
        self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller
    ) -> EntityShareNode:
        if laid.share is None:
            raise LookupError("this row needs a share laid in advance")
        with ActingAs(laid.caller):
            payload = await adapter.get(EntityShareID(laid.share.id))
        return payload.share


@dataclass(frozen=True)
class LoadingTheShare(When[ASharedFolderAndACaller, EntityShareAdapter, Loaded]):
    """그 공유를 id 로 한 번에 읽는다. ``missing`` 이면 없는 id 를 뒤에 붙인다."""

    missing: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        if self.missing:
            return Says(
                f"{laid.caller.username}이 공유 하나와 없는 id 하나를 한 번에 조회합니다",
                english=f"{laid.caller.username} loads one share and one unknown id at once",
            )
        return Says(
            f"{laid.caller.username}이 공유 하나를 한 번에 조회합니다",
            english=f"{laid.caller.username} loads one share at once",
        )

    @override
    async def call(self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller) -> Loaded:
        if laid.share is None:
            raise LookupError("this row needs a share laid in advance")
        ids = [EntityShareID(laid.share.id)]
        if self.missing:
            ids.append(EntityShareID(MISSING))
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ReadingRow(Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Read]):
    named: str
    guarantees: str
    situation: ASharedFolderAndSomeone

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, ASharedFolderAndACaller]:
        return self.situation

    @override
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Read]:
        return ReadingTheShare()

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Read]:
        return TheShareNode(started=STARTED, status=EntityShareStatusDTO.PENDING)


@dataclass(frozen=True)
class LoadingRow(Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Loaded]):
    named: str
    guarantees: str
    situation: ASharedFolderAndSomeone
    missing: bool = False
    refused: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, ASharedFolderAndACaller]:
        return self.situation

    @override
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Loaded]:
        return LoadingTheShare(missing=self.missing)

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Loaded]:
        if self.refused:
            return TheShareEntryIsRefused()
        return TheSharesComeBack(started=STARTED, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheShare(
    Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Read]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-share"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 공유를 조회하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing reads the share, the call is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASharedFolderAndACaller]:
        return ASharedFolderAndSomeone(who=Side.SOMEBODY)

    @override
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Read]:
        return ReadingTheShare()

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Read]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)
SHARER = ASharedFolderAndSomeone(who=Side.SHARER)
SOMEBODY = ASharedFolderAndSomeone(who=Side.SOMEBODY)

READS: list[ReadStep] = [
    ReadingRow(
        named="a-user-granted-on-the-project-reads-the-share",
        guarantees=Says(
            "프로젝트에서 공유 읽기 권한을 받은 사용자가 공유를 조회하면 그 공유가 통째로 옵니다",
            english=(
                "when a user granted share reading in the project reads the share, the whole "
                "share comes back"
            ),
        ),
        situation=SHARER,
    ),
    AUserGrantedNothingMayNotReadTheShare(),
]


LOADS: list[LoadStep] = [
    LoadingRow(
        named="a-user-granted-on-the-project-loads-the-share",
        guarantees=Says(
            "프로젝트에서 공유 읽기 권한을 받은 사용자가 id 로 조회하면 그 공유가 노드로 옵니다",
            english=(
                "when a user granted share reading in the project loads one by id, the share "
                "comes back as a node"
            ),
        ),
        situation=SHARER,
    ),
    LoadingRow(
        named="an-unknown-share-id-answers-a-denial",
        guarantees=Says(
            "id 로 읽으면 권한 검사를 거치므로, 없는 id 는 빈 값이 아니라 권한 부족으로 옵니다",
            english=(
                "a read by id is checked, so an id nothing answers to comes back as a denial "
                "rather than an empty value"
            ),
        ),
        situation=SHARER,
        missing=True,
    ),
    LoadingRow(
        named="a-user-granted-nothing-gets-a-denial-for-the-share",
        guarantees=Says(
            "아무 권한도 없는 사용자가 id 로 조회하면 그 자리는 권한 부족으로 옵니다",
            english=(
                "when a user granted nothing loads one by id, that entry is rejected for lack "
                "of permission"
            ),
        ),
        situation=SOMEBODY,
        refused=True,
    ),
]


@pytest.mark.parametrize("scenario", READS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", LOADS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
