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
    Refused,
    Same,
    TestGiven,
    TestScenario,
    TestThen,
    TestVerdict,
    TestWhen,
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
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[VFolderNode | Exception | None]
type LoadStep = TestScenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class LoadingTheFolderById(TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]):
    """폴더 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더 id로 일괄 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([VFolderUUID(laid.folder.id)])


@dataclass(frozen=True)
class LoadingReadableUnreadableAndMissing(TestWhen[AReaderAndTwoFolders, VFolderAdapter, Answer]):
    """닿을 수 있는 폴더, 닿을 수 없는 폴더, 없는 id 순으로 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AReaderAndTwoFolders) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.name}, {laid.unreadable.name}, "
            "없는 id 순으로 일괄 읽음"
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
class LoadingTheFolderAndMissing(TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]):
    """있는 폴더와 없는 id를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderAndItsReader) -> str:
        return f"{laid.caller.username}이 {laid.folder.name} 폴더와 없는 id를 일괄 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndItsReader) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                VFolderUUID(laid.folder.id),
                VFolderUUID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingNothing(TestWhen[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: AFolderMakerAndTheirDomain) -> str:
        return f"{laid.caller.username}이 빈 목록으로 일괄 읽음"

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderMakerAndTheirDomain) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class TheFolderAlone(TestThen[AFolderAndItsReader, Answer]):
    """심은 폴더 하나가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 폴더 하나가 통째로 온다"

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[TestVerdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[TestVerdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, VFolderNode):
            seen.extend(VFolderNodeLook(self.started).verdicts(first, laid.folder, at="[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "VFolderNode"))
        return seen


@dataclass(frozen=True)
class ARefusalAlone(TestThen[AFolderAndItsReader, Answer]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return "그 자리는 권한 부족으로 거부된다"

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[TestVerdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class EachElementInOrder(TestThen[AReaderAndTwoFolders, Answer]):
    """입력 순서대로 자리마다 폴더 또는 거부가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "입력 순서대로 자리마다 폴더 또는 거부가 온다"

    @override
    def look(self, laid: AReaderAndTwoFolders, answered: Answered[Answer]) -> list[TestVerdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[TestVerdict] = [Same("length", len(loaded), 3)]
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
class TheFolderThenNothing(TestThen[AFolderAndItsReader, Answer]):
    """있는 폴더는 노드로, 없는 id 자리는 빈 값으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "있는 폴더는 노드로, 없는 id 자리는 빈 값으로 온다"

    @override
    def look(self, laid: AFolderAndItsReader, answered: Answered[Answer]) -> list[TestVerdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[TestVerdict] = [Same("length", len(loaded), 2)]
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
class AnEmptyList(TestThen[AFolderMakerAndTheirDomain, Answer]):
    """빈 목록이 온다."""

    @override
    def says(self) -> str:
        return "빈 목록이 온다"

    @override
    def look(
        self, laid: AFolderMakerAndTheirDomain, answered: Answered[Answer]
    ) -> list[TestVerdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [])]


@dataclass(frozen=True)
class AUserLoadsTheirOwnFolderById(
    TestScenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-own-folder-by-id"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더 id로 일괄 읽기를 하면, "
            "그 폴더가 온다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> TestThen[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheirOwnFolder(
    TestScenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-their-own-folder"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 자기 폴더 id로 일괄 읽기를 하면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> TestThen[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class ABatchLoadAnswersEachElementInOrder(
    TestScenario[SeedingSession, AReaderAndTwoFolders, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-batch-load-answers-a-node-or-a-refusal-for-each-id-in-order"

    @override
    def describe(self) -> str:
        return (
            "자기 폴더만 읽을 수 있는 사용자가 자기 폴더, 공유받지 않은 남의 폴더, 없는 id를 "
            "한 번에 요청하면, 입력 순서대로 그 폴더, 거부, 거부가 온다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AReaderAndTwoFolders]:
        return SomeoneWithTheirFolderAndAnothers()

    @override
    def when(self) -> TestWhen[AReaderAndTwoFolders, VFolderAdapter, Answer]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> TestThen[AReaderAndTwoFolders, Answer]:
        return EachElementInOrder(started=self.started)


@dataclass(frozen=True)
class AnAcceptedShareLoadsSomeoneElsesFolderById(
    TestScenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-accepted-share-loads-someone-elses-folder-by-id"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더 id로 일괄 읽기를 하면, "
            "그 폴더가 온다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=True)

    @override
    def when(self) -> TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> TestThen[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AnUnansweredOfferGetsARefusalForTheFolder(
    TestScenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-unanswered-offer-gets-a-refusal-in-place-of-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더 id로 일괄 읽기를 하면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=False)

    @override
    def when(self) -> TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> TestThen[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class TheSuperadminBatchLoadLeavesAMissingIdEmpty(
    TestScenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 남의 폴더와 없는 id를 함께 요청하면, "
            "그 폴더는 노드로, 없는 id 자리는 빈 값으로 온다"
        )

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderAndItsReader]:
        return SomeonesFolderAndTheSuperadmin()

    @override
    def when(self) -> TestWhen[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderAndMissing()

    @override
    def then(self) -> TestThen[AFolderAndItsReader, Answer]:
        return TheFolderThenNothing(started=self.started)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    TestScenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 온다"

    @override
    def given(self) -> TestGiven[SeedingSession, AFolderMakerAndTheirDomain]:
        return SomeoneWithNoGrant()

    @override
    def when(self) -> TestWhen[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]:
        return LoadingNothing()

    @override
    def then(self) -> TestThen[AFolderMakerAndTheirDomain, Answer]:
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
