"""런타임 변형 지우기 — 하나씩, 그리고 여럿을 한 번에.

여럿 지우기는 하나 지우기를 id마다 되풀이하는 것이라 한 트랜잭션이 아니다. 답이 끝까지 성공한
뒤에만 오므로 답의 수는 요청한 id의 수와 같다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant import (
    AVariantAndACaller,
    AVariantAndSomeone,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    TheCountAsked,
    TheDeletedVariantId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant.request import DeleteRuntimeVariantsInput
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    DeleteRuntimeVariantPayload,
    DeleteRuntimeVariantsPayload,
)
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type RetiringStep = Scenario[SeedingSession, Any, RuntimeVariantAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]):
    """심은 변형 하나를 지운다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.variant.name
        return f"{laid.caller.username}이 {target}를 지움"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> DeleteRuntimeVariantPayload:
        with ActingAs(laid.caller):
            return await adapter.delete(uuid4() if self.unknown else laid.variant.id)


@dataclass(frozen=True)
class DeletingMany(
    When[ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload]
):
    """심은 변형 전부를 한 번에 지운다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 {len(laid.laid)}개를 한 번에 지움"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller
    ) -> DeleteRuntimeVariantsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_delete(
                DeleteRuntimeVariantsInput(ids=[one.id for one in laid.laid])
            )


@dataclass(frozen=True)
class DeletingWithAnUnknownIdBehind(
    When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload]
):
    """심은 변형의 id 뒤에 없는 id를 붙여 한 번에 지운다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.variant.name}와 없는 id를 한 번에 지움"

    @override
    async def call(
        self, adapter: RuntimeVariantAdapter, laid: AVariantAndACaller
    ) -> DeleteRuntimeVariantsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_delete(
                DeleteRuntimeVariantsInput(ids=[laid.variant.id, uuid4()])
            )


@dataclass(frozen=True)
class TheSuperadminDeletesAVariant(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-variant"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 변형을 지우면 지운 변형의 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]:
        return Deleting()

    @override
    def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantPayload]:
        return TheDeletedVariantId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]
):
    @override
    def summary(self) -> str:
        return "deleting-a-variant-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 변형도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-variant"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 변형을 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]:
        return Deleting()

    @override
    def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-variant"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 변형을 지운다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone()

    @override
    def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]:
        return Deleting()

    @override
    def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantPayload]:
        return TheDeletedVariantId()


@dataclass(frozen=True)
class ManyAreDeletedAtOnce(
    Scenario[
        SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-many-variants-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 변형 둘을 한 번에 지우면, 답은 요청한 id의 수를 그대로 싣는다"

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(
        self,
    ) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload]:
        return DeletingMany()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, DeleteRuntimeVariantsPayload]:
        return TheCountAsked()


@dataclass(frozen=True)
class AnUnknownIdInTheListIsNotFound(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "an-unknown-id-in-a-bulk-delete-is-not-found-after-the-ones-before-it-are-gone"

    @override
    def describe(self) -> str:
        return (
            "있는 id 뒤에 없는 id를 붙여 한 번에 지우면 대상이 없다는 것으로 거부된다. "
            "한 트랜잭션이 아니라 앞의 것은 이미 지워져 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AVariantAndACaller]:
        return AVariantAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload]:
        return DeletingWithAnUnknownIdBehind()

    @override
    def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteMany(
    Scenario[
        SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-many-variants"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 변형 둘을 한 번에 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=1)

    @override
    def when(
        self,
    ) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload]:
        return DeletingMany()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, DeleteRuntimeVariantsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAVariant(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
    EnforcementOffLetsAnyoneDelete(),
    ManyAreDeletedAtOnce(),
    AnUnknownIdInTheListIsNotFound(),
    AUserGrantedNothingMayNotDeleteMany(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
