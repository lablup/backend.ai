"""id 여러 개로 조회 — 순서와 빈 항목, 그리고 권한이 없을 때."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
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

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.response import ImageAliasNode, ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

MISSING_IMAGE = ImageID(uuid.UUID("00000000-0000-0000-0000-0000000000ff"))
MISSING_ALIAS = ImageAliasID(uuid.UUID("00000000-0000-0000-0000-0000000000fe"))

type LoadedImages = list[ImageNode | None]
type LoadedAliases = list[ImageAliasNode | None]


@dataclass(frozen=True)
class LoadingImages(When[ManyImagesAndACaller, ImageAdapter, LoadedImages]):
    """이미지 id 목록으로 한 번에 조회한다."""

    nothing_is_asked: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        who = laid.caller.username
        if self.nothing_is_asked:
            return f"{who}이 빈 id 목록으로 조회"
        return f"{who}이 미리 만들어 둔 이미지 2개와 없는 id 1개를 한 번에 조회"

    @override
    async def call(self, adapter: ImageAdapter, laid: ManyImagesAndACaller) -> LoadedImages:
        asked = (
            []
            if self.nothing_is_asked
            else [ImageID(laid.laid[0].id), MISSING_IMAGE, ImageID(laid.laid[1].id)]
        )
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(asked)


@dataclass(frozen=True)
class LoadingAliases(When[AnAliasAndACaller, ImageAdapter, LoadedAliases]):
    """별칭 id 목록으로 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_aliases_by_ids"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 미리 만들어 둔 별칭 1개와 없는 id 1개를 한 번에 조회"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> LoadedAliases:
        with ActingAs(laid.caller):
            return await adapter.batch_load_aliases_by_ids([
                ImageAliasID(laid.alias.id),
                MISSING_ALIAS,
            ])


@dataclass(frozen=True)
class TheImageOrderIsKept(Then[ManyImagesAndACaller, LoadedImages]):
    """요청한 순서대로 반환되고, 없는 id 위치는 비어 있다."""

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되고 없는 id 위치는 비어 있다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("length", len(got), 3),
            Same(
                "names",
                [one.name if one is not None else None for one in got],
                [laid.laid[0].name, None, laid.laid[1].name],
            ),
        ]


@dataclass(frozen=True)
class NothingIsAsked(Then[ManyImagesAndACaller, LoadedImages]):
    """빈 목록을 전달하면 빈 응답이 반환된다."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: ManyImagesAndACaller, answered: Answered[LoadedImages]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class TheAliasOrderIsKept(Then[AnAliasAndACaller, LoadedAliases]):
    """별칭도 같은 형태로 응답한다."""

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되고 없는 id 위치는 비어 있다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[LoadedAliases]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("length", len(got), 2),
            Same(
                "aliases",
                [one.alias if one is not None else None for one in got],
                [laid.alias.alias, None],
            ),
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
            "슈퍼관리자가 미리 만들어 둔 이미지 2개와 어느 이미지도 가리키지 않는 id 1개를 한 번에 "
            "조회하면, 요청한 순서대로 반환되고 없는 id 위치만 비어 있다"
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
        return "an-empty-image-id-list-answers-empty-without-calling-the-wiring"

    @override
    def describe(self) -> str:
        return "빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환된다"

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
class APlainUserIsRefusedWholesale(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, LoadedImages]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-image-ids-is-refused-as-a-whole"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 id 여러 개를 한 번에 조회하려 하면, "
            "원소별로 갈리지 않고 요청 전체가 역할 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, LoadedImages]:
        return LoadingImages()

    @override
    def then(self) -> Then[ManyImagesAndACaller, LoadedImages]:
        return TheCallIsRefused(InsufficientPrivilege)


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
            "슈퍼관리자가 미리 만들어 둔 별칭 1개와 어느 별칭도 가리키지 않는 id 1개를 한 번에 "
            "조회하면, 요청한 순서대로 반환되고 없는 id 위치만 비어 있다"
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
class APlainUserMayNotLoadAliases(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, LoadedAliases]
):
    @override
    def summary(self) -> str:
        return "a-plain-user-loading-many-alias-ids-is-refused-as-a-whole"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 별칭 id 여러 개를 한 번에 조회하려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, LoadedAliases]:
        return LoadingAliases()

    @override
    def then(self) -> Then[AnAliasAndACaller, LoadedAliases]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Any] = [
    LoadingKeepsTheOrderAndLeavesHoles(),
    AnEmptyListAsksNothing(),
    APlainUserIsRefusedWholesale(),
    LoadingAliasesKeepsTheOrderToo(),
    APlainUserMayNotLoadAliases(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine) -> None:
    await run_scenario(scenario, adapter, engine)
