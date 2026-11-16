"""폴더를 다른 사람에게 빌려주는 제안 — 제안이 서고, 아직 응답하지 않는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput,
    EntityShareRecipientInput,
)
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
    TheShareNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Offered = EntityShareNode
type OfferStep = Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Offered]


@dataclass(frozen=True)
class OfferingTheFolder(When[ASharedFolderAndACaller, EntityShareAdapter, Offered]):
    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 폴더 {laid.folder.name}를 {laid.recipient.username}에게 "
            "빌려주는 제안을 합니다",
            english=(
                f"{laid.caller.username} offers folder {laid.folder.name} to "
                f"{laid.recipient.username}"
            ),
        )

    @override
    async def call(
        self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller
    ) -> EntityShareNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateEntityShareInput(
                    target_entity_type=VFolderEntityType(),
                    target_entity_id=laid.folder.id,
                    recipient=EntityShareRecipientInput(user_id=laid.recipient.id),
                )
            )
        return payload.share


@dataclass(frozen=True)
class TheOfferStands(
    Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Offered]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-project-offers-the-folder"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 공유 생성 권한을 받은 사용자가 폴더를 다른 사람에게 제안하면 아직 "
            "응답하지 않은 공유가 통째로 옵니다",
            english=(
                "when a user granted share creation in the project offers the folder to another "
                "person, the unanswered share comes back whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASharedFolderAndACaller]:
        return ASharedFolderAndSomeone(who=Side.SHARER, offered=False)

    @override
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Offered]:
        return OfferingTheFolder()

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Offered]:
        return TheShareNode(started=STARTED, status=EntityShareStatusDTO.PENDING, fresh=True)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefused(
    Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Offered]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-cannot-offer-the-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 폴더를 제안하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing offers the folder, the call is rejected for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASharedFolderAndACaller]:
        return ASharedFolderAndSomeone(who=Side.SOMEBODY, offered=False)

    @override
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Offered]:
        return OfferingTheFolder()

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Offered]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[OfferStep] = [
    TheOfferStands(),
    AUserGrantedNothingIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: OfferStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
