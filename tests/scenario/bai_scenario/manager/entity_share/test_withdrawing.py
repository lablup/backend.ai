"""빌려준 쪽과 빌린 쪽이 공유를 끝내기 — 취소, 회수, 탈퇴."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

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
    TheShareNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Ended = EntityShareNode
type EndStep = Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Ended]


@dataclass(frozen=True)
class EndingTheShare(When[ASharedFolderAndACaller, EntityShareAdapter, Ended]):
    """``how`` 가 가리키는 호출로 공유를 끝낸다."""

    how: str

    @override
    def operation(self) -> str:
        return self.how

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        match self.how:
            case "cancel":
                how_ko = "응답하지 않은 제안을 취소합니다"
                how_en = "cancels the unanswered offer"
            case "revoke":
                how_ko = "빌려준 공유를 회수합니다"
                how_en = "takes back the share it lent"
            case _:
                how_ko = "빌린 공유에서 탈퇴합니다"
                how_en = "leaves the share it took"
        return Says(
            f"{laid.caller.username}이 폴더 {laid.folder.name}의 공유를 {how_ko}",
            english=f"{laid.caller.username} {how_en} of folder {laid.folder.name}",
        )

    @override
    async def call(
        self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller
    ) -> EntityShareNode:
        if laid.share is None:
            raise LookupError("this row needs a share laid in advance")
        share_id = EntityShareID(laid.share.id)
        with ActingAs(laid.caller):
            match self.how:
                case "cancel":
                    payload = await adapter.cancel(share_id)
                case "revoke":
                    payload = await adapter.revoke(share_id)
                case _:
                    payload = await adapter.leave(share_id)
        return payload.share


@dataclass(frozen=True)
class EndRow(Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Ended]):
    named: str
    guarantees: str
    situation: ASharedFolderAndSomeone
    how: str
    status: EntityShareStatusDTO
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
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Ended]:
        return EndingTheShare(how=self.how)

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Ended]:
        if self.refused:
            return TheCallIsRefused(NotEnoughPermission)
        return TheShareNode(started=STARTED, status=self.status)


STARTED = datetime.now(UTC)
SHARER = ASharedFolderAndSomeone(who=Side.SHARER)
RECIPIENT = ASharedFolderAndSomeone(who=Side.RECIPIENT)
SOMEBODY = ASharedFolderAndSomeone(who=Side.SOMEBODY)
TAKEN_SHARER = ASharedFolderAndSomeone(who=Side.SHARER, taken=True)
TAKEN_RECIPIENT = ASharedFolderAndSomeone(who=Side.RECIPIENT, taken=True)


SCENARIOS: list[EndStep] = [
    EndRow(
        named="the-sharer-cancels-the-unanswered-offer",
        guarantees=Says(
            "빌려준 사람이 응답하지 않은 제안을 취소하면 취소된 공유가 통째로 옵니다",
            english=(
                "when the lending side cancels the unanswered offer, the canceled share comes "
                "back whole"
            ),
        ),
        situation=SHARER,
        how="cancel",
        status=EntityShareStatusDTO.CANCELED,
    ),
    EndRow(
        named="the-sharer-takes-back-the-share",
        guarantees=Says(
            "빌려준 사람이 빌려준 공유를 회수하면 회수된 공유가 통째로 옵니다",
            english=(
                "when the lending side takes back the share, the revoked share comes back whole"
            ),
        ),
        situation=TAKEN_SHARER,
        how="revoke",
        status=EntityShareStatusDTO.REVOKED,
    ),
    EndRow(
        named="the-recipient-leaves-the-share",
        guarantees=Says(
            "빌린 사람이 자기 스코프에서 공유에서 탈퇴하면 회수된 공유가 통째로 옵니다",
            english=(
                "when the receiving side leaves the share in their own scope, the revoked share "
                "comes back whole"
            ),
        ),
        situation=TAKEN_RECIPIENT,
        how="leave",
        status=EntityShareStatusDTO.REVOKED,
    ),
    EndRow(
        named="a-user-granted-nothing-may-not-cancel-the-offer",
        guarantees=Says(
            "아무 권한도 없는 사용자가 제안을 취소하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing cancels the offer, the call is rejected for lack "
                "of permission"
            ),
        ),
        situation=SOMEBODY,
        how="cancel",
        status=EntityShareStatusDTO.CANCELED,
        refused=True,
    ),
    EndRow(
        named="a-user-granted-nothing-may-not-take-the-share-back",
        guarantees=Says(
            "아무 권한도 없는 사용자가 공유를 회수하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing takes the share back, the call is rejected for "
                "lack of permission"
            ),
        ),
        situation=ASharedFolderAndSomeone(who=Side.SOMEBODY, taken=True),
        how="revoke",
        status=EntityShareStatusDTO.REVOKED,
        refused=True,
    ),
    EndRow(
        named="a-user-granted-nothing-may-not-leave-the-share",
        guarantees=Says(
            "아무 권한도 없는 사용자가 공유에서 탈퇴해도 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing leaves the share, the call is rejected for lack "
                "of permission"
            ),
        ),
        situation=SOMEBODY,
        how="leave",
        status=EntityShareStatusDTO.REVOKED,
        refused=True,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_withdrawing(
    scenario: EndStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
