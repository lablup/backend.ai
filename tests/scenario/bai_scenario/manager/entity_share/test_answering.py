"""받는 쪽의 두 가지 답 — 받아들이면 공유가 서고, 거절하면 서지 않는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.dto.manager.v2.entity_share.response import EntityShareNode
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
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

type Answered = EntityShareNode
type AnswerStep = Scenario[
    TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Answered
]


@dataclass(frozen=True)
class AnsweringTheOffer(When[ASharedFolderAndACaller, EntityShareAdapter, Answered]):
    """그 제안에 답한다. ``accepting`` 이면 받아들이고 아니면 거절한다."""

    accepting: bool

    @override
    def operation(self) -> str:
        if self.accepting:
            return "accept"
        return "reject"

    @override
    def describe(self, laid: ASharedFolderAndACaller) -> str:
        answer = "받아들입니다" if self.accepting else "거절합니다"
        answer_en = "accepts" if self.accepting else "rejects"
        return Says(
            f"{laid.caller.username}이 폴더 {laid.folder.name}의 공유 제안을 {answer}",
            english=(f"{laid.caller.username} {answer_en} the offer of folder {laid.folder.name}"),
        )

    @override
    async def call(
        self, adapter: EntityShareAdapter, laid: ASharedFolderAndACaller
    ) -> EntityShareNode:
        if laid.share is None:
            raise LookupError("this row needs an offer laid in advance")
        with ActingAs(laid.caller):
            if self.accepting:
                payload = await adapter.accept(EntityShareID(laid.share.id))
            else:
                payload = await adapter.reject(EntityShareID(laid.share.id))
        return payload.share


@dataclass(frozen=True)
class AnswerRow(
    Scenario[TestSeedingSession, ASharedFolderAndACaller, EntityShareAdapter, Answered]
):
    named: str
    guarantees: str
    situation: ASharedFolderAndSomeone
    accepting: bool
    refused_with: type[BaseException] | None = None

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
    def when(self) -> When[ASharedFolderAndACaller, EntityShareAdapter, Answered]:
        return AnsweringTheOffer(accepting=self.accepting)

    @override
    def then(self) -> Then[ASharedFolderAndACaller, Answered]:
        if self.refused_with is not None:
            return TheCallIsRefused(self.refused_with)
        status = EntityShareStatusDTO.ACCEPTED if self.accepting else EntityShareStatusDTO.REJECTED
        return TheShareNode(started=STARTED, status=status)


STARTED = datetime.now(UTC)
RECIPIENT = ASharedFolderAndSomeone(who=Side.RECIPIENT)
SOMEBODY = ASharedFolderAndSomeone(who=Side.SOMEBODY)
PROJECT_RECIPIENT = ASharedFolderAndSomeone(who=Side.RECIPIENT, to_a_project=True)
PROJECT_READER = ASharedFolderAndSomeone(
    who=Side.RECIPIENT, to_a_project=True, recipient_granted=(Permission.READ,)
)

SCENARIOS: list[AnswerStep] = [
    AnswerRow(
        named="the-recipient-accepts-the-offer",
        guarantees=Says(
            "자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 받아들이면 받아들인 공유가 "
            "통째로 옵니다",
            english=(
                "when a user who can answer shares in their own scope accepts the offer, the "
                "accepted share comes back whole"
            ),
        ),
        situation=RECIPIENT,
        accepting=True,
    ),
    AnswerRow(
        named="the-recipient-rejects-the-offer",
        guarantees=Says(
            "자기 스코프에서 공유에 답할 수 있는 사용자가 제안을 거절하면 거절된 공유가 통째로 "
            "옵니다",
            english=(
                "when a user who can answer shares in their own scope rejects the offer, the "
                "rejected share comes back whole"
            ),
        ),
        situation=RECIPIENT,
        accepting=False,
    ),
    AnswerRow(
        named="a-user-granted-nothing-may-not-accept-the-offer",
        guarantees=Says(
            "아무 권한도 없는 사용자가 제안을 받아들이면 공유를 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing accepts the offer, it is rejected because the share "
                "cannot be resolved"
            ),
        ),
        situation=SOMEBODY,
        accepting=True,
        refused_with=GenericBadRequest,
    ),
    AnswerRow(
        named="a-user-granted-nothing-may-not-reject-the-offer",
        guarantees=Says(
            "아무 권한도 없는 사용자가 제안을 거절해도 공유를 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing rejects the offer, it is rejected because the share "
                "cannot be resolved"
            ),
        ),
        situation=SOMEBODY,
        accepting=False,
        refused_with=GenericBadRequest,
    ),
    AnswerRow(
        named="a-project-answerer-accepts-the-offer-to-the-project",
        guarantees=Says(
            "프로젝트 앞으로 온 제안을 그 프로젝트에서 공유에 답할 수 있는 사용자가 받아들이면 "
            "받아들인 공유가 통째로 옵니다",
            english=(
                "when a user who can answer shares in a project accepts an offer addressed to "
                "that project, the accepted share comes back whole"
            ),
        ),
        situation=PROJECT_RECIPIENT,
        accepting=True,
    ),
    AnswerRow(
        named="a-project-answerer-rejects-the-offer-to-the-project",
        guarantees=Says(
            "프로젝트 앞으로 온 제안을 그 프로젝트에서 공유에 답할 수 있는 사용자가 거절하면 "
            "거절된 공유가 통째로 옵니다",
            english=(
                "when a user who can answer shares in a project rejects an offer addressed to "
                "that project, the rejected share comes back whole"
            ),
        ),
        situation=PROJECT_RECIPIENT,
        accepting=False,
    ),
    AnswerRow(
        named="a-project-reader-may-not-accept-the-offer-to-the-project",
        guarantees=Says(
            "프로젝트 앞으로 온 제안을 그 프로젝트에서 공유를 읽을 수만 있는 사용자가 받아들이면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user who can only read shares in a project accepts an offer addressed to "
                "that project, the call is rejected for lack of permission"
            ),
        ),
        situation=PROJECT_READER,
        accepting=True,
        refused_with=NotEnoughPermission,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_answering(
    scenario: AnswerStep, adapter: EntityShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
