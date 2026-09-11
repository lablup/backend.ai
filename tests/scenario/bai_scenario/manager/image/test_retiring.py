"""이미지 지우기 — 행까지 없애고, 별칭도 함께 사라진다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AnAliasAndACaller,
    AnAliasAndSomeone,
    AnIdThatHoldsNothing,
    AnImageAndACaller,
    AnImageAndSomeone,
    AnImageNobodyOwns,
    AnImageTheCallerMade,
    Target,
    TheImageNode,
    TheLaidImage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import PurgeImageInput
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.image import ImageAccessForbiddenError, ImageNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)


@dataclass(frozen=True)
class Retiring(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 지운다. 행이 사라지고 되살릴 수 없다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}를 지움"
        return f"{who}이 {laid.image.name}을 지움"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_purge(PurgeImageInput(image_id=target))
        return payload.item


@dataclass(frozen=True)
class RetiringTheAliased(When[AnAliasAndACaller, ImageAdapter, ImageNode]):
    """별칭이 붙은 이미지를 지운다."""

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 별칭 {laid.alias.alias}가 붙은 이미지를 지움"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> ImageNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_purge(PurgeImageInput(image_id=laid.image.id))
        return payload.item


@dataclass(frozen=True)
class TheRetiredImageComesBack(Then[AnAliasAndACaller, ImageNode]):
    """지운 이미지가 답으로 온다."""

    @override
    def says(self) -> str:
        return "지운 이미지가 답으로 온다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[ImageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("name", node.name, laid.image.name),
            Same("registry", node.registry, laid.image.registry),
            Same("architecture", node.architecture, laid.image.architecture),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("last_used_at", "세션이 쓰는 값이라 이 실행이 말할 수 없다"),
        ]


@dataclass(frozen=True)
class PurgingAnswersWithTheRemovedImage(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "purging-an-image-answers-with-the-image-it-removed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이미지를 지우면 지워진 이미지가 답으로 오고 되살릴 수 없다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode()


@dataclass(frozen=True)
class TheMakerOfACustomImageMayPurgeIt(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "the-maker-of-a-custom-image-may-purge-it"

    @override
    def describe(self) -> str:
        return (
            "자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 지우면, "
            "게이트와 소유권 검사를 모두 지나 지워진 이미지가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageTheCallerMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode()


@dataclass(frozen=True)
class PurgingTakesTheAliasesWithIt(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "purging-an-image-takes-its-aliases-with-it"

    @override
    def describe(self) -> str:
        return (
            "별칭이 붙은 이미지도 지워지고 지워진 이미지가 답으로 온다. "
            "별칭이 함께 사라지는 것은 답에 실리지 않아 이 행이 보지 못한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, ImageNode]:
        return RetiringTheAliased()

    @override
    def then(self) -> Then[AnAliasAndACaller, ImageNode]:
        return TheRetiredImageComesBack()


@dataclass(frozen=True)
class RetiringWhatIsNotThere(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "purging-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "아무 이미지도 갖지 않은 id를 지우려 하면 이미지가 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class AnUngrantedUserMayNotRetire(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-an-image"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이미지를 지우려 하면 권한 부족으로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantIsNotOwnershipHereEither(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-may-not-purge-an-image-nobody-owns"

    @override
    def describe(self) -> str:
        return (
            "주인 없는 이미지는 그 이미지에 권한을 받은 사용자라도 지울 수 없다. "
            "게이트를 지난 뒤 소유권 검사가 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageAccessForbiddenError)


SCENARIOS: list[Any] = [
    PurgingAnswersWithTheRemovedImage(),
    TheMakerOfACustomImageMayPurgeIt(),
    PurgingTakesTheAliasesWithIt(),
    RetiringWhatIsNotThere(),
    AnUngrantedUserMayNotRetire(),
    AGrantIsNotOwnershipHereEither(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: Any,
    adapter: ImageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
