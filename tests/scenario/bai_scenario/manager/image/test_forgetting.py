"""이미지 잊기와 되살리기 — 게이트를 지난 뒤에도 소유권 검사가 남는다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
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
from ai.backend.common.dto.manager.v2.image.request import ForgetImageInput, RestoreImageInput
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import ImageAccessForbiddenError, ImageNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

ENFORCEMENT = "manager.rbac.enforcement_enabled"


@dataclass(frozen=True)
class Forgetting(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 잊는다. 행은 남고 상태만 바뀐다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "admin_forget"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}를 잊음"
        return f"{who}이 {laid.image.name}을 잊음"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_forget(ForgetImageInput(image_id=target))
        return payload.item


@dataclass(frozen=True)
class Restoring(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """잊은 이미지를 되살린다."""

    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "admin_restore"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}를 되살림"
        return f"{who}이 {laid.image.name}을 되살림"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_restore(RestoreImageInput(image_id=target))
        return payload.item


@dataclass(frozen=True)
class ForgettingMarksItDeletedAndKeepsTheRow(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "forgetting-an-image-marks-it-deleted-and-keeps-the-row"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이미지를 잊으면, 행은 남고 지워졌다는 상태를 실은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class TheMakerOfACustomImageMayForgetIt(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "the-maker-of-a-custom-image-may-forget-it"

    @override
    def describe(self) -> str:
        return (
            "자기가 만든 커스텀 이미지에 권한까지 받은 사용자가 그것을 잊으면, "
            "게이트와 소유권 검사를 모두 지나 지워졌다는 상태가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageTheCallerMade()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.DELETED)


@dataclass(frozen=True)
class AForgottenImageCannotBeReached(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "restoring-a-forgotten-image-cannot-reach-it"

    @override
    def describe(self) -> str:
        return (
            "잊힌 이미지를 되살리려 하면 이미지가 없다는 이유로 거부된다. "
            "이미지를 id로 집는 자리가 살아 있는 것만 보기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN, status=ImageStatus.DELETED)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class RestoringWhatWasNeverForgotten(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "restoring-an-image-that-was-never-forgotten-leaves-it-alive"

    @override
    def describe(self) -> str:
        return "살아 있는 이미지를 되살려도 살아 있는 그대로다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(status=ImageStatus.ALIVE)


@dataclass(frozen=True)
class ForgettingWhatIsNotThere(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "forgetting-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "아무 이미지도 갖지 않은 id를 잊으려 하면 이미지가 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class RestoringWhatIsNotThere(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "restoring-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "아무 이미지도 갖지 않은 id를 되살리려 하면 이미지가 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring(at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class AnUngrantedUserMayNotForget(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-forget-an-image"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이미지를 잊으려 하면 권한 부족으로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUngrantedUserMayNotRestore(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-an-image"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 이미지를 되살리려 하면 권한 부족으로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Restoring()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantIsNotOwnership(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "a-granted-user-may-not-forget-an-image-nobody-owns"

    @override
    def describe(self) -> str:
        return (
            "커스터마이즈되지 않은 이미지는 주인이 없으므로, "
            "그 이미지에 권한을 받은 사용자라도 게이트를 지난 뒤 소유권 검사에서 막힌다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageAccessForbiddenError)


@dataclass(frozen=True)
class EnforcementOffDoesNotReachOwnership(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-does-not-let-anyone-forget-an-unowned-image"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 꺼서 게이트를 열어도 주인 없는 이미지는 잊을 수 없다. "
            "소유권 검사는 그 스위치가 닿지 않는 자리에서 돌기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageNobodyOwns(granted=False)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageAccessForbiddenError)


@dataclass(frozen=True)
class AnImageBeingPurgedIsNotVisible(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "an-image-a-purge-is-working-through-cannot-be-reached"

    @override
    def describe(self) -> str:
        return (
            "지우는 중인 이미지를 잊으려 하면 이미지가 없다는 이유로 거부된다. "
            "그 상태의 이미지는 id로 집는 자리에서 보이지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN, status=ImageStatus.PURGING)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Forgetting()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


SCENARIOS: list[Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]] = [
    ForgettingMarksItDeletedAndKeepsTheRow(),
    TheMakerOfACustomImageMayForgetIt(),
    AForgottenImageCannotBeReached(),
    RestoringWhatWasNeverForgotten(),
    ForgettingWhatIsNotThere(),
    RestoringWhatIsNotThere(),
    AnUngrantedUserMayNotForget(),
    AnUngrantedUserMayNotRestore(),
    AGrantIsNotOwnership(),
    EnforcementOffDoesNotReachOwnership(),
    AnImageBeingPurgedIsNotVisible(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_forgetting(
    scenario: Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode],
    adapter: ImageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
