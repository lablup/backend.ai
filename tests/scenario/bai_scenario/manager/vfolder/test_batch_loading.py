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
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[VFolderNode | Exception | None]
type LoadStep = Scenario[SeedingSession, Any, VFolderAdapter, Answer]


@dataclass(frozen=True)
class LoadingTheFolderById(When[AFolderAndItsReader, VFolderAdapter, Answer]):
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
class LoadingReadableUnreadableAndMissing(When[AReaderAndTwoFolders, VFolderAdapter, Answer]):
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
class LoadingTheFolderAndMissing(When[AFolderAndItsReader, VFolderAdapter, Answer]):
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
class LoadingNothing(When[AFolderMakerAndTheirDomain, VFolderAdapter, Answer]):
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
class TheFolderAlone(Then[AFolderAndItsReader, Answer]):
    """자리 하나에 심은 폴더가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "자리 하나에 심은 폴더 전체가 온다"

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
    """호출은 답하고, 자리 하나에 권한 부족 거부가 온다."""

    @override
    def says(self) -> str:
        return "자리 하나에 권한 부족 거부가 온다"

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
    """자리마다 폴더와 거부가 입력 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "자리마다 결과가 입력 순서대로 온다"

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
    """있는 폴더는 노드, 없는 id 자리는 비어서 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "있는 폴더는 노드, 없는 id 자리는 비어서 온다"

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
        return "빈 목록이 온다"

    @override
    def look(self, laid: AFolderMakerAndTheirDomain, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [])]


@dataclass(frozen=True)
class AUserLoadsTheirOwnFolderById(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-loads-their-own-folder-by-id"

    @override
    def describe(self) -> str:
        return (
            "자기 개인 프로젝트에서 폴더 읽기 권한을 받은 사용자가 자기 폴더 id로 일괄 읽으면, "
            "그 자리에 그 폴더가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheirOwnFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-their-own-folder"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 자기 폴더 id로 일괄 읽으면, "
            "호출은 답하되 그 자리에 권한 부족 거부가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return SomeoneWithAFolderOfTheirOwn(granted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class ABatchLoadAnswersEachElementInOrder(
    Scenario[SeedingSession, AReaderAndTwoFolders, VFolderAdapter, Answer]
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
    def given(self) -> Given[SeedingSession, AReaderAndTwoFolders]:
        return SomeoneWithTheirFolderAndAnothers()

    @override
    def when(self) -> When[AReaderAndTwoFolders, VFolderAdapter, Answer]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> Then[AReaderAndTwoFolders, Answer]:
        return EachElementInOrder(started=self.started)


@dataclass(frozen=True)
class AnAcceptedShareLoadsSomeoneElsesFolderById(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-accepted-share-loads-someone-elses-folder-by-id"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더를 읽기로 공유받아 받아들인 사용자가 그 폴더 id로 일괄 읽으면, "
            "그 자리에 그 폴더가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=True)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderAlone(started=self.started)


@dataclass(frozen=True)
class AnUnansweredOfferGetsARefusalForTheFolder(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-unanswered-offer-gets-a-refusal-in-place-of-someone-elses-folder"

    @override
    def describe(self) -> str:
        return (
            "남의 폴더를 공유 제안만 받고 받아들이지 않은 사용자가 그 폴더 id로 일괄 읽으면, "
            "호출은 답하되 그 자리에 권한 부족 거부가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return AFolderOfferedToSomeone(accepted=False)

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderById()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return ARefusalAlone()


@dataclass(frozen=True)
class TheSuperadminBatchLoadLeavesAMissingIdEmpty(
    Scenario[SeedingSession, AFolderAndItsReader, VFolderAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 남의 폴더와 없는 id를 함께 요청하면, "
            "권한 문을 지나 없는 원소 자리에 빈 값이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AFolderAndItsReader]:
        return SomeonesFolderAndTheSuperadmin()

    @override
    def when(self) -> When[AFolderAndItsReader, VFolderAdapter, Answer]:
        return LoadingTheFolderAndMissing()

    @override
    def then(self) -> Then[AFolderAndItsReader, Answer]:
        return TheFolderThenNothing(started=self.started)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[SeedingSession, AFolderMakerAndTheirDomain, VFolderAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 검사에 닿기 전에 빈 목록이 온다"

    @override
    def given(self) -> Given[SeedingSession, AFolderMakerAndTheirDomain]:
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
