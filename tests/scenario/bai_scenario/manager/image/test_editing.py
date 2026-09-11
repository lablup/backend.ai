"""이미지 고치기 — 준 것만 바뀌고, 가속기만 세 갈래를 받는다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    Accelerators,
    AnIdThatHoldsNothing,
    AnImageAndACaller,
    AnImageAndSomeone,
    NoAccelerator,
    OneAccelerator,
    Target,
    TheImageNode,
    TheLaidImage,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import UpdateImageInput
from ai.backend.common.dto.manager.v2.image.response import ImageNode
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Scenario,
    Then,
    When,
)

A_NEW_TAG = "moved"


@dataclass(frozen=True)
class Editing(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 고친다. 값을 주지 않은 자리는 건드리지 않는다."""

    tag: str | None = None
    accelerators: Accelerators | None = None
    at: Target = field(default_factory=TheLaidImage)

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.at, AnIdThatHoldsNothing):
            return f"{who}이 {self.at.says()}를 고침"
        if self.accelerators is not None:
            named = self.accelerators.named()
            put = "비움" if named is None else f"{named}로 적음"
            return f"{who}이 {laid.image.name}의 가속기 목록을 {put}"
        if self.tag is not None:
            return f"{who}이 {laid.image.name}의 태그를 {self.tag}로 고침"
        return f"{who}이 아무 값도 주지 않고 고침"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = self.at.id_of(laid)
        asked: dict[str, Any] = {"image_id": target}
        if self.tag is not None:
            asked["tag"] = self.tag
        if self.accelerators is not None:
            asked["supported_accelerators"] = self.accelerators.named()
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(UpdateImageInput(**asked))
        return payload.item


@dataclass(frozen=True)
class ChangingOnlyTheTag(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "changing-only-the-tag-leaves-every-other-field-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 태그만 고치면 태그만 새 값이 되고 나머지 자리는 그대로다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(tag=A_NEW_TAG)

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(tag=A_NEW_TAG)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "an-edit-that-names-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 값을 하나도 주지 않고 고치면 아무것도 바뀌지 않은 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing()

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode()


@dataclass(frozen=True)
class ClearingTheAcceleratorList(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "clearing-the-accelerator-list-empties-it"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 가속기 목록을 비우는 수정을 하면 그 자리가 빈 채로 온다. "
            "생략과 비우기를 따로 말할 수 있는 항목은 이것뿐이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN, accelerators=OneAccelerator())

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(accelerators=NoAccelerator())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode()


@dataclass(frozen=True)
class WritingTheAcceleratorList(
    Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]
):
    @override
    def summary(self) -> str:
        return "writing-an-accelerator-onto-an-image-that-had-none"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 가속기 이름을 주면 그 이름이 적힌 노드가 온다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(accelerators=OneAccelerator())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheImageNode(accelerators=OneAccelerator())


@dataclass(frozen=True)
class EditingWhatIsNotThere(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "editing-an-id-that-holds-no-image-is-refused"

    @override
    def describe(self) -> str:
        return "아무 이미지도 갖지 않은 id를 고치려 하면 이미지가 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(tag=A_NEW_TAG, at=AnIdThatHoldsNothing())

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(ImageNotFound)


@dataclass(frozen=True)
class APlainUserMayNotEdit(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-an-image"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 이미지를 고치려 하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, AnImageAndACaller]:
        return AnImageAndSomeone()

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(tag=A_NEW_TAG)

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Any] = [
    ChangingOnlyTheTag(),
    AnEmptyEditChangesNothing(),
    ClearingTheAcceleratorList(),
    WritingTheAcceleratorList(),
    EditingWhatIsNotThere(),
    APlainUserMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine) -> None:
    await run_scenario(scenario, adapter, engine)
