"""이미지 완전 삭제 요청과 응답을 검증한다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import PurgeImageInput
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.image import ImageAccessForbiddenError, ImageNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AnAliasAndACaller,
    AnAliasAndSomeone,
    AnIdThatHoldsNothing,
    AnImageAndACaller,
    AnImageAndSomeone,
    AnImageTheCallerMade,
    AnUncustomizedImageAndSomeone,
    Target,
    TheImageNode,
    TheLaidImage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class Retiring(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 완전 삭제한다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()} 완전 삭제"
        return f"{who}이 {laid.image.name} 완전 삭제"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_purge(PurgeImageInput(image_id=target))
        return payload.item


@dataclass(frozen=True)
class RetiringTheAliased(When[AnAliasAndACaller, ImageAdapter, ImageNode]):
    """별칭이 등록된 이미지를 완전 삭제한다."""

    @override
    def operation(self) -> str:
        return "admin_purge"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 별칭 {laid.alias.alias}가 등록된 이미지를 완전 삭제"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnAliasAndACaller) -> ImageNode:
        with ActingAs(laid.caller):
            payload = await adapter.admin_purge(PurgeImageInput(image_id=laid.image.id))
        return payload.item


@dataclass(frozen=True)
class PurgingAnswersWithTheRemovedImage(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "purging-an-image-answers-with-the-image-it-removed"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이미지를 완전 삭제하면 삭제된 이미지가 반환된다"

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
            "자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 완전 삭제하면, "
            "이미지 권한과 커스텀 이미지 작성자 검사를 모두 통과해 삭제된 이미지가 반환된다"
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
class PurgingAnAliasedImageReturnsTheRemovedImage(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "purging-an-aliased-image-answers-with-the-image-it-removed"

    @override
    def describe(self) -> str:
        return "별칭이 등록된 이미지를 완전 삭제하면 삭제된 이미지가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, ImageNode]:
        return RetiringTheAliased()

    @override
    def then(self) -> Then[AnAliasAndACaller, ImageNode]:
        return TheImageNode()


@dataclass(frozen=True)
class RetiringWhatIsNotThere(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "purging-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "어느 이미지도 가리키지 않는 ID를 완전 삭제하려 하면 대상을 찾을 수 없어 거부된다"

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
        return "아무 권한도 받지 않은 사용자가 이미지를 완전 삭제하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnUncustomizedImageAndSomeone(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantDoesNotSkipTheCreatorCheck(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-may-not-purge-an-image-they-did-not-customize"

    @override
    def describe(self) -> str:
        return (
            "커스텀 이미지가 아닌 이미지는 권한을 받은 사용자라도 완전 삭제할 수 없다. "
            "이미지 권한 검사를 통과한 뒤 커스텀 이미지 작성자 검사에서 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnUncustomizedImageAndSomeone()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Retiring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageAccessForbiddenError)


SCENARIOS: list[Any] = [
    PurgingAnswersWithTheRemovedImage(),
    TheMakerOfACustomImageMayPurgeIt(),
    PurgingAnAliasedImageReturnsTheRemovedImage(),
    RetiringWhatIsNotThere(),
    AnUngrantedUserMayNotRetire(),
    AGrantDoesNotSkipTheCreatorCheck(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: Any,
    adapter: ImageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
