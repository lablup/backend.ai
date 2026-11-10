"""런타임 변형 수정 — 무엇이 바뀌고 무엇이 그대로 남으며, 누가 수정할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant.request import UpdateRuntimeVariantInput
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "renamed"

type EditingStep = Scenario[TestSeedingSession, Any, RuntimeVariantAdapter, RuntimeVariantNode]


@dataclass(frozen=True)
class Editing(When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]):
    """미리 만들어 둔 변형을 수정한다. 응답에 담긴 노드를 꺼내서 준다."""

    named: str | None = None
    described: str | Unset | None = UNSET
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.variant.name
        target_en = "an unknown id" if self.unknown else laid.variant.name
        changing = []
        changing_en = []
        if self.named is not None:
            changing.append("이름")
            changing_en.append("name")
        if not isinstance(self.described, Unset):
            changing.append("설명")
            changing_en.append("description")
        if not changing:
            return Says(
                f"{laid.caller.username}이 {target}을 변경 값 없이 수정합니다",
                english=f"{laid.caller.username} updates {target_en} without giving a value",
            )
        return Says(
            f"{laid.caller.username}이 {target}의 {' 및 '.join(changing)}을 수정합니다",
            english=(f"{laid.caller.username} updates the {', '.join(changing_en)} of {target_en}"),
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.named.name}의 이름을 {other.name}(으)로 수정합니다",
            english=f"{laid.caller.username} renames {laid.named.name} to {other.name}",
        )

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
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "renaming-a-variant-leaves-its-description-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 인퍼런스 런타임 종류의 이름만 바꾸면, 이름은 새 값이 되고 설명은 그대로 "
            "유지됩니다",
            english=(
                "when the superadmin changes only the name of a runtime variant, the name takes "
                "the new value and the description stays"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ClearingTheDescription(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-a-variant-description-leaves-it-empty"

    @override
    def describe(self) -> str:
        return Says(
            "설명이 있는 인퍼런스 런타임 종류에 설명을 비우는 수정을 하면, 설명이 없어집니다",
            english=(
                "when a runtime variant that has a description is updated to clear it, "
                "the description is gone"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(described=None)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started, described=None)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-giving-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 반환됩니다",
            english=("when an update gives no value, the node comes back with nothing changed"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing()

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheVariantNode(started=self.started)


@dataclass(frozen=True)
class RenamingToATakenNameIsRefused(
    Scenario[TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "renaming-a-variant-to-a-name-already-taken-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "인퍼런스 런타임 종류 둘 중 한쪽의 이름을 다른 쪽 이름으로 바꾸면, 이름 중복으로 "
            "거부됩니다. 생성할 때와 달리 저장소의 제약 위반이 그대로 전파됩니다",
            english=(
                "when one of two runtime variants is renamed to the other's name, it is rejected "
                "as a duplicate name. Unlike on creation, the repository's constraint violation "
                "propagates as is"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return RenamingToAnothersName()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(UniqueConstraintViolationError)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownIdIsNotFound(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-variant-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 수정하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin updates an id that nothing answers to, it is rejected "
                "because the target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-variant"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 인퍼런스 런타임 종류를 수정하면 권한 부족으로 거부됩니다. "
            "인퍼런스 런타임 종류는 어느 스코프에도 속하지 않아 그 권한을 받을 방법이 없습니다",
            english=(
                "when a user granted nothing updates a runtime variant, it is rejected for lack "
                "of permission. A runtime variant belongs to no scope, so there is no way to "
                "grant that permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingEditingAnUnknownIdIsRefusedTheSameWay(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-editing-an-unknown-variant-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 존재하지 않는 id 를 수정하면 대상 없음이 아니라 권한 부족으로 "
            "거부됩니다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문입니다",
            english=(
                "when a user granted nothing updates an unknown id, it is rejected for lack of "
                "permission, not as a missing target. The permission check runs first, and no "
                "permission is granted on a row that does not exist"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode]:
        return Editing(named=RENAMED, unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, RuntimeVariantNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneEdit(
    Scenario[TestSeedingSession, AVariantAndACaller, RuntimeVariantAdapter, RuntimeVariantNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-edit-a-variant"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 인퍼런스 런타임 종류를 수정할 수 있습니다",
            english=(
                "turning the permission check off lets even a user granted nothing update "
                "a runtime variant"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
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
