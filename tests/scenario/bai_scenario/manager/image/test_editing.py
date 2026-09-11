"""이미지 고치기 — 준 것만 바뀌고, 가속기만 세 갈래를 받는다."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AnImageAndACaller,
    AnImageAndSomeone,
    TheImageNode,
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

MISSING = uuid.UUID("00000000-0000-0000-0000-0000000000ff")
A_NEW_TAG = "moved"


@dataclass(frozen=True)
class Editing(When[AnImageAndACaller, ImageAdapter, ImageNode]):
    """이미지를 고친다. 값을 주지 않은 자리는 건드리지 않는다."""

    tag: str | None = None
    clearing_accelerators: bool = False
    at_missing: bool = False

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: AnImageAndACaller) -> str:
        who = laid.caller.username
        if self.at_missing:
            return f"{who}이 아무것도 갖지 않은 id를 고침"
        if self.clearing_accelerators:
            return f"{who}이 {laid.image.name}의 가속기 목록을 비움"
        if self.tag is not None:
            return f"{who}이 {laid.image.name}의 태그를 {self.tag}로 고침"
        return f"{who}이 아무 값도 주지 않고 고침"

    @override
    async def call(self, adapter: ImageAdapter, laid: AnImageAndACaller) -> ImageNode:
        target = MISSING if self.at_missing else laid.image.id
        asked: dict[str, Any] = {"image_id": target}
        if self.tag is not None:
            asked["tag"] = self.tag
        if self.clearing_accelerators:
            asked["supported_accelerators"] = None
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(UpdateImageInput(**asked))
        return payload.item


@dataclass(frozen=True)
class TheTagIsTheOnlyChange(Then[AnImageAndACaller, ImageNode]):
    """태그만 새 값이 되고 나머지는 그대로다."""

    tag: str

    @override
    def says(self) -> str:
        return "태그만 새 값이고 나머지는 그대로다"

    @override
    def look(self, laid: AnImageAndACaller, answered: Answered[ImageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("name", node.name, laid.image.name),
            Same("registry", node.registry, laid.image.registry),
            Same("architecture", node.architecture, laid.image.architecture),
            Same("tag", node.tag, self.tag),
            Same("status", node.status, laid.image.status),
            Same("is_local", node.is_local, laid.image.is_local),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("last_used_at", "세션이 쓰는 값이라 이 실행이 말할 수 없다"),
        ]


@dataclass(frozen=True)
class NoAcceleratorsAreLeft(Then[AnImageAndACaller, ImageNode]):
    """가속기 자리가 빈 채로 온다."""

    @override
    def says(self) -> str:
        return "가속기 자리가 비어 있다"

    @override
    def look(self, laid: AnImageAndACaller, answered: Answered[ImageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("name", node.name, laid.image.name),
            Same("accelerators", node.accelerators, None),
            Same("tag", node.tag, laid.image.tag),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("last_used_at", "세션이 쓰는 값이라 이 실행이 말할 수 없다"),
        ]


@dataclass(frozen=True)
class TheTagIsChanged(Scenario[SeedingSession, AnImageAndACaller, ImageAdapter, ImageNode]):
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
        return TheTagIsTheOnlyChange(tag=A_NEW_TAG)


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
class TheAcceleratorsAreCleared(
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
        return AnImageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnImageAndACaller, ImageAdapter, ImageNode]:
        return Editing(clearing_accelerators=True)

    @override
    def then(self) -> Then[AnImageAndACaller, ImageNode]:
        return NoAcceleratorsAreLeft()


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
        return Editing(tag=A_NEW_TAG, at_missing=True)

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
    TheTagIsChanged(),
    AnEmptyEditChangesNothing(),
    TheAcceleratorsAreCleared(),
    EditingWhatIsNotThere(),
    APlainUserMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine) -> None:
    await run_scenario(scenario, adapter, engine)
