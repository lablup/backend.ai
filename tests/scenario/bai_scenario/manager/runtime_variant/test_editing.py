"""런타임 변형 수정 — 무엇이 바뀌고 무엇이 그대로 남으며, 누가 수정할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant import (
    AVariantAndACaller,
    AVariantAndSomeone,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    TheVariantNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant.request import UpdateRuntimeVariantInput
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

RENAMED = "renamed"

type EditingStep = Scenario[SeedingSession, Any, RuntimeVariantAdapter, RuntimeVariantNode]


@dataclass(frozen=True)
class Editing(When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]):
    """미리 만들어 둔 변형을 수정한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str | None = None
    described: str | Sentinel | None = SENTINEL
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.variant.name
        changing = []
        if self.named is not None:
            changing.append("이름")
        if not isinstance(self.described, Sentinel):
            changing.append("설명")
        return f"{laid.caller.username}이 {target}의 {' 및 '.join(changing) or '아무것도'} 수정"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> RuntimeVariantNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateRuntimeVariantInput(
                    id=uuid4() if self.unknown else laid.variant.id,
                    name=self.named,
                    description=self.described,
                )
            )
        return payload.runtime_variant


@dataclass(frozen=True)
class RenamingToAnothersName(
    When[ManyVariantsAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    """골라낸 하나의 이름을 함께 만들어 둔 다른 변형의 이름으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        return f"{laid.caller.username}이 {laid.named.name}의 이름을 {other.name}(으)로 수정"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller
    ) -> RuntimeVariantNode:
        other = next(one for one in laid.laid if one.id != laid.named.id)
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateRuntimeVariantInput(id=laid.named.id, name=other.name)
            )
        return payload.runtime_variant


@dataclass(frozen=True)
class TheNameChangesAndTheDescriptionStays(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "renaming-a-variant-leaves-its-description-alone"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 변형의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 유지된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-variant-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return "설명이 있는 변형에 설명을 비우는 수정을 하면, 설명이 없어진다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(described=None)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started, described=None)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return "값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started)


@dataclass(frozen=True)
class RenamingToATakenNameIsRefused(
    Scenario[SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "renaming-a-variant-to-a-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return (
            "변형 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름 중복으로 거부된다. "
            "생성할 때와 달리 저장소의 제약 위반이 그대로 전파된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return RenamingToAnothersName()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-variant"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 변형을 수정하면 권한 부족으로 거부된다. "
            "변형은 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingEditingAnUnknownIdIsRefusedTheSameWay(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id를 수정하면 대상 없음이 아니라 권한 부족으로 "
            "거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-variant"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 변형을 수정할 수 있다. "
            "수정은 역할이 아니라 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started, named=RENAMED)


SCENARIOS: list[EditingStep] = [
    TheNameChangesAndTheDescriptionStays(started=datetime.now(UTC)),
    ClearingTheDescription(started=datetime.now(UTC)),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    RenamingToATakenNameIsRefused(),
    TheSuperadminEditingAnUnknownIdIsNotFound(),
    AUserGrantedNothingMayNotEdit(),
    AUserGrantedNothingEditingAnUnknownIdIsRefusedTheSameWay(),
    EnforcementOffLetsAnyoneEdit(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
