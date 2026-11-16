"""폴더 여러 개를 id로 한 번에 읽기 — 자리마다 무엇이 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.vfolder import (
    AFolderAndItsReader,
    AFolderMakerAndTheirDomain,
    AFolderOfferedToSomeone,
    AReaderAndTwoFolders,
    SomeonesFolderAndTheSuperadmin,
    SomeoneWithAFolderOfTheirOwn,
    SomeoneWithNoGrant,
    SomeoneWithTheirFolderAndAnothers,
    VFolderNodeLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[VFolderNode | Exception | None]
type LoadStep = Scenario[TestSeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class LoadingTheFolderById(When[AFolderAndItsReader, VFolderAdapter, Answer]):
    """폴더 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 id 로 일괄 조회합니다",
            english=f"{laid.caller.username} loads the {laid.folder.name} vfolder by id in one call",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class LoadingReadableUnreadableAndMissing(When[AReaderAndTwoFolders, VFolderAdapter, Answer]):
    """닿을 수 있는 폴더, 닿을 수 없는 폴더, 없는 id 순으로 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AReaderAndTwoFolders) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.readable.name}, {laid.unreadable.name}, "
            "없는 id 순으로 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads a readable vfolder, an unreadable vfolder and "
                "a missing id in that order in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AReaderAndTwoFolders) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                VFolderUUID(laid.readable.id),
                VFolderUUID(laid.unreadable.id),
                VFolderUUID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingTheFolderAndMissing(When[AFolderAndItsReader, VFolderAdapter, Answer]):
    """있는 폴더와 없는 id를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 와 없는 id 를 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the {laid.folder.name} vfolder and a missing id "
                "in one call"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                VFolderUUID(laid.folder.id),
                VFolderUUID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingNothing(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return Says(
            f"{laid.caller.username}이 빈 목록으로 일괄 조회합니다",
            english=f"{laid.caller.username} loads with an empty list",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheFolderAlone(Then[AFolderAndItsReader, Answer]):
    """심은 폴더 하나가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 vfolder 하나가 전체가 응답으로 옵니다",
            english="the whole vfolder seeded in advance comes back",
        )

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, VFolderNode):
            seen.extend(VFolderNodeLook(self.started).verdicts(first, laid.folder, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "VFolderNode"))
        return seen


@dataclass(frozen=True)
class ARefusalAlone(Then[AFolderAndItsReader, Answer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class EachElementInOrder(Then[AReaderAndTwoFolders, Answer]):
    """입력 순서대로 자리마다 폴더 또는 거부가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "입력 순서대로 각 항목에 vfolder 또는 거부가 옵니다",
            english="a vfolder or a rejection comes back for each id in input order",
        )

    @override
    def look(self, laid: AReaderAndTwoFolders, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 3)]
        if len(loaded) != 3:
            return seen
        first, second, third = loaded
        if isinstance(first, VFolderNode):
            seen.extend(VFolderNodeLook(self.started).verdicts(first, laid.readable, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "VFolderNode"))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        seen.append(Refused(NotEnoughPermission, third if isinstance(third, Exception) else None))
        return seen


@dataclass(frozen=True)
class TheFolderThenNothing(Then[AFolderAndItsReader, Answer]):
    """있는 폴더는 노드로, 없는 id 자리는 빈 값으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "있는 vfolder 는 노드로, 없는 id 항목은 빈 값으로 옵니다",
            english=(
                "the existing vfolder comes back as a node and the missing id entry as an "
                "empty value"
            ),
        )

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return seen
        first, second = loaded
        if isinstance(first, VFolderNode):
            seen.extend(VFolderNodeLook(self.started).verdicts(first, laid.folder, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "VFolderNode"))
        seen.append(Same("[1]", second, None))
        return seen


@dataclass(frozen=True)
class AnEmptyList(Then[AFolderMakerAndTheirDomain, Answer]):
    """빈 목록이 온다."""

    @override
    def says(self) -> str:
        return Says("빈 목록이 옵니다", english="an empty list comes back")

    @override
    def look(self, laid: AFolderMakerAndTheirDomain, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [])]


@dataclass(frozen=True)
class AUserLoadsTheirOwnFolderById(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-own-folder-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "자기 개인 프로젝트에서 vfolder 읽기 권한을 받은 사용자가 자기 vfolder 를 id 로 "
            "일괄 조회하면, 그 vfolder 가 응답으로 옵니다",
            english=(
                "when a user granted vfolder read in their personal project loads their own "
                "vfolder by id, that vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheirOwnFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-in-place-of-their-own-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 vfolder 를 id 로 일괄 조회하면, 호출은 "
            "성공하되 그 항목은 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing loads their own vfolder by id, the call succeeds "
                "but that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class ABatchLoadAnswersEachElementInOrder(
    Scenario[TestSeedingSession, AReaderAndTwoFolders, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-batch-load-answers-a-node-or-a-rejection-for-each-id-in-order"

    @override
    def describe(self) -> str:
        return Says(
            "자기 vfolder 만 읽을 수 있는 사용자가 자기 vfolder, 공유받지 않은 다른 사용자의 "
            "vfolder, 없는 id 를 한 번에 요청하면, 입력 순서대로 그 vfolder, 거부, 거부가 옵니다",
            english=(
                "when a user who can read only their own vfolder asks for their vfolder, "
                "someone else's unshared vfolder and a missing id in one call, their vfolder, "
                "a rejection and a rejection come back in input order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AReaderAndTwoFolders]:
        return SomeoneWithTheirFolderAndAnothers()

    @override
    def when(self) -> When[AReaderAndTwoFolders, VFolderAdapter, Answer]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> Then[AReaderAndTwoFolders, Answer]:
        return EachElementInOrder(started=self.started)


@dataclass(frozen=True)
class AnAcceptedShareLoadsSomeoneElsesFolderById(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-accepted-share-loads-someone-elses-folder-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사용자의 vfolder 를 읽기로 공유받아 받아들인 사용자가 그 vfolder 를 id 로 "
            "일괄 조회하면, 그 vfolder 가 응답으로 옵니다",
            english=(
                "when a user who accepted a read share of someone else's vfolder loads it by "
                "id, that vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AnUnansweredOfferGetsARefusalForTheFolder(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-unanswered-offer-gets-a-rejection-in-place-of-someone-elses-folder"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사용자의 vfolder 를 공유 제안만 받고 받아들이지 않은 사용자가 그 vfolder 를 "
            "id 로 일괄 조회하면, 호출은 성공하되 그 항목은 권한 부족으로 거부됩니다",
            english=(
                "when a user who was offered someone else's vfolder but did not accept loads "
                "it by id, the call succeeds but that entry is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class TheSuperadminBatchLoadLeavesAMissingIdEmpty(
    Scenario[TestSeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 다른 사용자의 vfolder 와 없는 id 를 함께 요청하면, 그 vfolder 는 "
            "노드로, 없는 id 항목은 빈 값으로 옵니다",
            english=(
                "when the superadmin asks for someone else's vfolder and a missing id "
                "together, the vfolder comes back as a node and the missing id entry as an "
                "empty value"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndItsReader]:
        return SomeonesFolderAndTheSuperadmin()

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderAndMissing()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderThenNothing(started=self.started)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[TestSeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 옵니다",
            english=(
                "when a user granted nothing gives an empty id list, an empty list comes back "
                "without a permission check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWithNoGrant()

    @override
    def when(self) -> When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return LoadingNothing()

    @override
    def then(self) -> Then[AFolderMakerAndTheirDomain, Answer]:
        return AnEmptyList()


STARTED = datetime.now(UTC)

SCENARIOS: list[LoadStep] = [
    AUserLoadsTheirOwnFolderById(started=STARTED),
    AUserGrantedNothingGetsARefusalForTheirOwnFolder(),
    ABatchLoadAnswersEachElementInOrder(started=STARTED),
    AnAcceptedShareLoadsSomeoneElsesFolderById(started=STARTED),
    AnUnansweredOfferGetsARefusalForTheFolder(),
    TheSuperadminBatchLoadLeavesAMissingIdEmpty(started=STARTED),
    ABatchLoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
