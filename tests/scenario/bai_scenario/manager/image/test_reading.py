"""ID 여러 개로 조회 — 순서와 빈 항목, 그리고 원소마다 오는 거부."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.response import ImageAliasNode, ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.image import (
    AnAliasAndACaller,
    AnAliasAndSomeone,
    Filled,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_IMAGE = ImageID(uuid.UUID("00000000-0000-0000-0000-0000000000ff"))
MISSING_ALIAS = ImageAliasID(uuid.UUID("00000000-0000-0000-0000-0000000000fe"))

type LoadedImages = list[ImageNode | Exception | None]
type LoadedAliases = list[ImageAliasNode | Exception | None]


@dataclass(frozen=True)
class LoadingImages(When[ManyImagesAndACaller, ImageAdapter, LoadedImages]):
    """이미지 ID 목록으로 한 번에 조회한다."""

    nothing_is_asked: bool = False
    duplicate_is_asked: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        who = laid.caller.username
        if self.nothing_is_asked:
            return f"{who}이 빈 ID 목록으로 조회"
        if self.duplicate_is_asked:
            return f"{who}이 같은 이미지 ID를 두 번 조회"
        return f"{who}이 미리 만들어 둔 이미지 2개와 없는 ID 1개를 한 번에 조회"

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> LoadedImages:
        if self.nothing_is_asked:
            asked = []
        elif self.duplicate_is_asked:
            asked = [ImageID(laid.named.id), ImageID(laid.named.id)]
        else:
            asked = [ImageID(laid.laid[0].id), MISSING_IMAGE, ImageID(laid.laid[1].id)]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class LoadingAliases(When[AnAliasAndACaller, ImageAdapter, LoadedAliases]):
    """별칭 ID 목록으로 한 번에 조회한다."""

    nothing_is_asked: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_aliases_by_ids"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        if self.nothing_is_asked:
            return f"{laid.caller.username}이 빈 별칭 ID 목록으로 조회"
        return f"{laid.caller.username}이 미리 만들어 둔 별칭 1개와 없는 ID 1개를 한 번에 조회"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> LoadedAliases:
        asked = [] if self.nothing_is_asked else [ImageAliasID(laid.alias.id), MISSING_ALIAS]
        with ActingAs(laid.caller):
            return await adapter.batch_load_aliases_by_ids(asked)


@dataclass(frozen=True)
class TheImageOrderIsKept(Then[ManyImagesAndACaller, LoadedImages]):
    """요청한 순서대로 반환되고, 있는 ID 자리에는 그 이미지가 온다."""

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되고 있는 ID 자리에는 그 이미지가 온다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        first, _, third = got
        return [
            Same("length", len(got), 3),
            Same(
                "[0].name", first.name if isinstance(first, ImageNode) else None, laid.laid[0].name
            ),
            Skipped("[1]", "없는 id에 superadmin이 받는 답은 아직 정해지지 않았다"),
            Same(
                "[2].name", third.name if isinstance(third, ImageNode) else None, laid.laid[1].name
            ),
        ]


@dataclass(frozen=True)
class EachImageIsRefused(Then[ManyImagesAndACaller, LoadedImages]):
    """원소마다 권한 부족 거부가 온다."""

    @override
    def says(self) -> str:
        return "원소마다 권한 부족 거부가 입력 순서대로 온다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [Same("length", len(got), 3)] + [
            Refused(NotEnoughPermission, one if isinstance(one, Exception) else None) for one in got
        ]


@dataclass(frozen=True)
class NothingIsAsked(Then[ManyImagesAndACaller, LoadedImages]):
    """빈 목록을 전달하면 빈 목록이 반환된다."""

    @override
    def says(self) -> str:
        return "빈 목록이 반환된다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class NoAliasesAreAsked(Then[AnAliasAndACaller, LoadedAliases]):
    """빈 별칭 ID 목록을 전달하면 빈 목록이 반환된다."""

    @override
    def says(self) -> str:
        return "빈 목록이 반환된다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[LoadedAliases]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class TheDuplicateImageIsReturnedTwice(Then[ManyImagesAndACaller, LoadedImages]):
    """같은 ID를 두 번 요청하면 같은 이미지가 두 위치에 반환된다."""

    @override
    def says(self) -> str:
        return "같은 이미지가 두 위치에 반환된다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("length", len(got), 2),
            Same(
                "names",
                [one.name if isinstance(one, ImageNode) else None for one in got],
                [str(laid.named.name), str(laid.named.name)],
            ),
        ]


@dataclass(frozen=True)
class TheAliasOrderIsKept(Then[AnAliasAndACaller, LoadedAliases]):
    """별칭은 요청한 순서대로 반환되고 없는 ID 위치는 비어 있다."""

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되고 없는 ID 위치는 비어 있다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[LoadedAliases]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("length", len(got), 2),
            Same(
                "aliases",
                [one.alias if isinstance(one, ImageAliasNode) else None for one in got],
                [laid.alias.alias, None],
            ),
        ]


@dataclass(frozen=True)
class TheAliasIsRefusedAndTheHoleStays(Then[AnAliasAndACaller, LoadedAliases]):
    """있는 별칭 자리에는 권한 부족 거부가, 없는 ID 자리에는 빈 값이 온다."""

    @override
    def says(self) -> str:
        return "있는 별칭 자리에는 권한 부족 거부가, 없는 ID 자리에는 빈 값이 온다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[LoadedAliases]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        first, second = got
        return [
            Same("length", len(got), 2),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
            Same("[1]", second, None),
        ]


@dataclass(frozen=True)
class LoadingKeepsTheOrderAndLeavesHoles(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, LoadedImages]
):
    @override
    def summary(self) -> str:
        return "loading-many-image-ids-keeps-the-order-and-leaves-a-hole"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미리 만들어 둔 이미지 2개와 어느 이미지도 가리키지 않는 ID 1개를 한 번에 "
            "조회하면, 요청한 순서대로 반환되고 있는 ID 자리에는 그 이미지가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, LoadedImages]:
        return LoadingImages()

    @override
    def then(self) -> Then[ManyImagesAndACaller, LoadedImages]:
        return TheImageOrderIsKept()


@dataclass(frozen=True)
class AnEmptyListAsksNothing(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, LoadedImages]
):
    @override
    def summary(self) -> str:
        return "an-empty-image-id-list-answers-with-an-empty-list"

    @override
    def describe(self) -> str:
        return "빈 ID 목록으로 조회하면 빈 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, LoadedImages]:
        return LoadingImages(nothing_is_asked=True)

    @override
    def then(self) -> Then[ManyImagesAndACaller, LoadedImages]:
        return NothingIsAsked()


@dataclass(frozen=True)
class APlainUserIsRefusedPerElement(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, LoadedImages]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-image-ids-is-refused-per-element"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 ID 여러 개를 한 번에 조회하면, "
            "요청 전체가 아니라 원소마다 권한 부족 거부가 입력 순서대로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, LoadedImages]:
        return LoadingImages()

    @override
    def then(self) -> Then[ManyImagesAndACaller, LoadedImages]:
        return EachImageIsRefused()


@dataclass(frozen=True)
class DuplicateImageIdsKeepBothPositions(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, LoadedImages]
):
    @override
    def summary(self) -> str:
        return "duplicate-image-ids-keep-both-input-positions"

    @override
    def describe(self) -> str:
        return "같은 이미지 ID를 두 번 조회하면 같은 이미지가 두 위치에 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=1)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, LoadedImages]:
        return LoadingImages(duplicate_is_asked=True)

    @override
    def then(self) -> Then[ManyImagesAndACaller, LoadedImages]:
        return TheDuplicateImageIsReturnedTwice()


@dataclass(frozen=True)
class LoadingAliasesKeepsTheOrderToo(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, LoadedAliases]
):
    @override
    def summary(self) -> str:
        return "loading-many-alias-ids-keeps-the-order-and-leaves-a-hole"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 미리 만들어 둔 별칭 1개와 어느 별칭도 가리키지 않는 ID 1개를 한 번에 "
            "조회하면, 요청한 순서대로 반환되고 없는 ID 위치만 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, LoadedAliases]:
        return LoadingAliases()

    @override
    def then(self) -> Then[AnAliasAndACaller, LoadedAliases]:
        return TheAliasOrderIsKept()


@dataclass(frozen=True)
class APlainUserIsRefusedPerAlias(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, LoadedAliases]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-alias-ids-is-refused-per-element"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 별칭 ID 여러 개를 한 번에 조회하면, "
            "있는 별칭 자리에는 권한 부족 거부가 오고 없는 ID 자리는 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, LoadedAliases]:
        return LoadingAliases()

    @override
    def then(self) -> Then[AnAliasAndACaller, LoadedAliases]:
        return TheAliasIsRefusedAndTheHoleStays()


@dataclass(frozen=True)
class AnEmptyAliasListAsksNothing(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, LoadedAliases]
):
    @override
    def summary(self) -> str:
        return "an-empty-alias-id-list-answers-with-an-empty-list"

    @override
    def describe(self) -> str:
        return "빈 별칭 ID 목록으로 조회하면 빈 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, LoadedAliases]:
        return LoadingAliases(nothing_is_asked=True)

    @override
    def then(self) -> Then[AnAliasAndACaller, LoadedAliases]:
        return NoAliasesAreAsked()


SCENARIOS: list[Any] = [
    LoadingKeepsTheOrderAndLeavesHoles(),
    AnEmptyListAsksNothing(),
    DuplicateImageIdsKeepBothPositions(),
    APlainUserIsRefusedPerElement(),
    LoadingAliasesKeepsTheOrderToo(),
    AnEmptyAliasListAsksNothing(),
    APlainUserIsRefusedPerAlias(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine) -> None:
    await run_scenario(scenario, adapter, engine)
