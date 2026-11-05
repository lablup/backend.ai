"""공유 훑기 — 내가 선 쪽으로, 또는 이름을 댄 범위로."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.dto.manager.v2.entity_share.request import (
    EntityShareScope,
    EntityShareTargetScope,
    MySearchEntitySharesInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.response import SearchEntitySharesPayload
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareSideDTO
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.entity_share import (
    ASharedFolderAndACaller,
    ASharedFolderAndSomeone,
    Side,
    TheSearchedShares,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Found = SearchEntitySharesPayload
type SearchStep = Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Found]


@dataclass(frozen=True)
class SearchingTheShares(When[ASharedFolderAndACaller, EntityShareAdapter, Found]):
    """``how`` 가 가리키는 갈래로 공유를 훑는다."""

    how: str

    @override
    def operation(self) -> str:
        return self.how

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        if self.how == "my_search":
            return Says(
                f"{laid.caller.username}이 자기가 선 쪽의 공유를 훑습니다",
                english=f"{laid.caller.username} pages through the shares of their own side",
            )
        return Says(
            f"{laid.caller.username}이 폴더 {laid.folder.name}에 걸린 공유를 훑습니다",
            english=f"{laid.caller.username} pages through the shares of folder {laid.folder.name}",
        )

    @override
    async def call(self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller) -> Found:
        with ActingAs(laid.caller):
            if self.how == "my_search":
                return await adapter.my_search(
                    MySearchEntitySharesInput(sides=[EntityShareSideDTO.RECIPIENT])
                )
            return await adapter.scoped_search(
                ScopedSearchEntitySharesInput(
                    scope=EntityShareScope(
                        target=[
                            EntityShareTargetScope(
                                entity_type=VFolderEntityType(),
                                entity_id=UUID(str(laid.folder.id)),
                            )
                        ]
                    )
                )
            )


@dataclass(frozen=True)
class SearchRow(Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Found]):
    named: str
    guarantees: str
    situation: ASharedFolderAndSomeone
    how: str
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
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Found]:
        return SearchingTheShares(how=self.how)

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Found]:
        if self.refused:
            return TheCallIsRefused(NotEnoughPermission)
        return TheSearchedShares(started=STARTED)


STARTED = datetime.now(UTC)
RECIPIENT = ASharedFolderAndSomeone(who=Side.RECIPIENT)
SHARER = ASharedFolderAndSomeone(who=Side.SHARER)
SOMEBODY = ASharedFolderAndSomeone(who=Side.SOMEBODY)

SCENARIOS: list[SearchStep] = [
    SearchRow(
        named="the-recipient-pages-through-the-shares-addressed-to-them",
        guarantees=Says(
            "자기 스코프에서 공유를 읽을 수 있는 사용자가 자기에게 온 공유를 훑으면 그 공유가 "
            "통째로 옵니다",
            english=(
                "when a user who can read shares in their own scope pages through the ones "
                "addressed to them, the share comes back whole"
            ),
        ),
        situation=RECIPIENT,
        how="my_search",
    ),
    SearchRow(
        named="the-sharer-pages-through-the-shares-of-a-folder",
        guarantees=Says(
            "프로젝트에서 공유를 읽을 수 있는 사용자가 폴더를 범위로 훑으면 그 폴더에 걸린 공유가 "
            "통째로 옵니다",
            english=(
                "when a user who can read shares in the project pages through a folder, the "
                "shares of that folder come back whole"
            ),
        ),
        situation=SHARER,
        how="scoped_search",
    ),
    SearchRow(
        named="a-user-granted-nothing-may-not-page-through-their-shares",
        guarantees=Says(
            "아무 권한도 없는 사용자가 자기에게 온 공유를 훑으면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing pages through the shares addressed to them, the "
                "call is rejected for lack of permission"
            ),
        ),
        situation=SOMEBODY,
        how="my_search",
        refused=True,
    ),
    SearchRow(
        named="a-user-granted-nothing-may-not-page-through-a-folders-shares",
        guarantees=Says(
            "아무 권한도 없는 사용자가 폴더를 범위로 훑으면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing pages through a folder, the call is rejected for "
                "lack of permission"
            ),
        ),
        situation=SOMEBODY,
        how="scoped_search",
        refused=True,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
