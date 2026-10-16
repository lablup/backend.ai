"""이미지 소프트 삭제와 복원 — 이미지 권한을 검사한다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AnIdThatHoldsNothing,
    AnImageAndACaller,
    AnImageAndSomeone,
    AnImageSomeoneElseMade,
    AnImageTheCallerMade,
    AnUncustomizedImageAndSomeone,
    Target,
    TheImageNode,
    TheLaidImage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class Forgetting(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 소프트 삭제한다. 행은 남고 상태만 바뀐다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()} 소프트 삭제"
        return f"{who}이 {laid.image.name} 소프트 삭제"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.delete(ImageID(target))
        return payload.item


@dataclass(frozen=True)
class Restoring(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """소프트 삭제한 이미지를 복원한다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "restore"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()} 복원"
        return f"{who}이 {laid.image.name} 복원"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.restore(ImageID(target))
        return payload.item


@dataclass(frozen=True)
class ForgettingMarksItDeletedAndKeepsTheRow(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "forgetting-an-image-marks-it-deleted-and-keeps-the-row"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이미지를 소프트 삭제하면, 행은 남고 삭제됨 상태가 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class TheMakerOfACustomImageMayForgetIt(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "the-maker-of-a-custom-image-may-forget-it"

    @override
    def describe(self) -> str:
        return (
            "자기가 커밋한 커스텀 이미지를 자기 개인 프로젝트의 권한으로 소프트 삭제하면, "
            "이미지가 그 개인 프로젝트에 속하므로 이미지 권한 검사를 통과해 삭제됨 상태가 반환된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageTheCallerMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class AnotherUsersCustomImageMayNotBeForgotten(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-may-not-forget-a-custom-image-another-user-made"

    @override
    def describe(self) -> str:
        return (
            "다른 사용자가 커밋한 커스텀 이미지는 그 사람의 개인 프로젝트에 속하므로, "
            "자기 개인 프로젝트에서 권한을 받은 사용자가 소프트 삭제하려 하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageSomeoneElseMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RestoringBringsAForgottenImageBack(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "restoring-a-forgotten-image-brings-it-back-alive"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 삭제된 이미지를 복원하면 살아 있는 상태가 담긴 노드가 반환된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN, status=ImageStatus.DELETED)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.ALIVE)


@dataclass(frozen=True)
class RestoringWhatWasNeverForgotten(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "restoring-an-image-that-was-never-forgotten-leaves-it-alive"

    @override
    def describe(self) -> str:
        return "살아 있는 이미지를 복원해도 살아 있는 상태 그대로다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.ALIVE)


@dataclass(frozen=True)
class ForgettingWhatIsNotThere(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "forgetting-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "어느 이미지도 가리키지 않는 ID를 소프트 삭제하려 하면 대상을 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class RestoringWhatIsNotThere(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "restoring-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "어느 이미지도 가리키지 않는 ID를 복원하려 하면 대상을 찾을 수 없어 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AnUngrantedUserMayNotForget(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-forget-an-image"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이미지를 소프트 삭제하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnUncustomizedImageAndSomeone(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUngrantedUserMayNotRestore(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-an-image"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이미지를 복원하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnUncustomizedImageAndSomeone(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserMayForgetAnImageTheyDidNotMake(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-may-forget-an-image-they-did-not-customize"

    @override
    def describe(self) -> str:
        return (
            "레지스트리에서 이미지 권한을 받은 사용자는 커스텀 이미지가 아닌 이미지도 "
            "소프트 삭제할 수 있고, 삭제됨 상태가 반환된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnUncustomizedImageAndSomeone()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class AnImageBeingPurgedIsNotVisible(
    Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "an-image-a-purge-is-working-through-cannot-be-reached"

    @override
    def describe(self) -> str:
        return (
            "완전 삭제 중인 이미지를 소프트 삭제하려 하면 대상을 찾을 수 없어 거부된다. "
            "살아 있는 이미지만 소프트 삭제할 수 있다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN, status=ImageStatus.PURGING)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


SCENARIOS: list[Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]] = [
    ForgettingMarksItDeletedAndKeepsTheRow(),
    TheMakerOfACustomImageMayForgetIt(),
    AnotherUsersCustomImageMayNotBeForgotten(),
    RestoringBringsAForgottenImageBack(),
    RestoringWhatWasNeverForgotten(),
    ForgettingWhatIsNotThere(),
    RestoringWhatIsNotThere(),
    AnUngrantedUserMayNotForget(),
    AnUngrantedUserMayNotRestore(),
    AGrantedUserMayForgetAnImageTheyDidNotMake(),
    AnImageBeingPurgedIsNotVisible(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_forgetting(
    scenario: Scenario[TestSeedingSession, AnImageAndACaller, ImageAdapter, ImageNode],
    adapter: ImageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
