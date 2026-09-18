"""런타임 변형 삭제 — 하나씩, 그리고 여럿을 한 번에.

일괄 삭제는 id마다 따로 답한다. 없는 id와 권한이 없는 id는 실패 목록에 들어가고, 나머지는
삭제된 채 삭제된 목록에 들어간다. 호출 자체는 거부되지 않는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant import (
    AVariantAndACaller,
    AVariantAndSomeone,
    EveryLaidVariantIsDeleted,
    EveryLaidVariantIsRefused,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    TheDeletedVariantId,
    TheLaidOneIsDeletedTheUnknownFails,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[SeedingSession, Any, RuntimeVariantAdapter, Any]


@dataclass(frozen=True)
class Deleting(When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]):
    """미리 만들어 둔 변형 하나를 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        target = "존재하지 않는 id" if self.unknown else laid.variant.name
        return f"{laid.caller.username}이 {target} 삭제"

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
    """미리 만들어 둔 변형 전부를 한 번에 삭제한다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 {len(laid.laid)}개를 한 번에 삭제"

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
    """미리 만들어 둔 변형의 id 뒤에 없는 id를 붙여 한 번에 삭제한다."""

    @override
    def operation(self) -> str:
        return "bulk_delete"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.variant.name}(와)과 없는 id를 한 번에 삭제"

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
        return "슈퍼관리자가 변형을 삭제하면 삭제한 변형의 id를 담은 응답이 반환된다"

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
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"

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
        return "아무 권한도 없는 사용자가 변형을 삭제하면 권한 부족으로 거부된다"

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
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 변형을 삭제할 수 있다"

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
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-many-variants-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 변형 둘을 한 번에 삭제하면, 둘 다 삭제된 목록에 반환되고 실패 목록은 비어 있다"

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
        return EveryLaidVariantIsDeleted(started=self.started)


@dataclass(frozen=True)
class AnUnknownIdInTheListFailsAlone(
    Scenario[
        SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-unknown-id-in-a-bulk-delete-fails-alone-while-the-known-one-is-deleted"

    @override
    def describe(self) -> str:
        return (
            "있는 id 뒤에 없는 id를 붙여 한 번에 삭제하면, 있는 것은 삭제된 목록에, "
            "없는 id는 실패 목록에 반환된다"
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
        return TheLaidOneIsDeletedTheUnknownFails(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingHasEveryVariantRefused(
    Scenario[
        SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-has-every-variant-refused-in-a-bulk-delete"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 변형 둘을 한 번에 삭제하면, 둘 다 실패 목록에 반환되고 "
            "아무것도 삭제되지 않는다"
        )

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
        return EveryLaidVariantIsRefused()


# TODO(BA-7931): enable once the preset seed from #14536 has landed and the ORM column
# carries the foreign key its migration declares. Until then the row cannot import its
# seed, and a schema built by ``metadata.create_all()`` does not cascade the presets.
# The Given moves to ``components/runtime_variant.py`` next to ``AVariantAndSomeone``.
#
# @dataclass(frozen=True)
# class AVariantWithAPresetAndSomeone(Given[Any, AVariantAndACaller]):
#     """변형 하나, 그 변형의 preset 하나, 사용자 한 명."""
#
#     role: UserRole = UserRole.USER
#
#     @override
#     def describe(self) -> str:
#         return f"preset 하나가 딸린 런타임 변형 하나와, {role_named(self.role)} 한 명"
#
#     @override
#     async def lay(self, seeding: Any) -> AVariantAndACaller:
#         variant = await seeding.creating(
#             SeedRuntimeVariant(name_hint="variant", description=DESCRIBED)
#         )
#         await seeding.creating_from(SeedRuntimeVariantPreset(), variant)
#         caller = await lay_a_caller(seeding, self.role)
#         return AVariantAndACaller(seeding.made(variant), seeding.made(caller))
#
#
# @dataclass(frozen=True)
# class AVariantWithAPresetGoesWithIt(
#     Scenario[SeedingSession, AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]
# ):
#     @override
#     def summary(self) -> str:
#         return "deleting-a-variant-takes-its-preset-with-it"
#
#     @override
#     def describe(self) -> str:
#         return "슈퍼관리자가 preset이 딸린 변형을 삭제하면 preset도 함께 사라지고, 삭제한 변형의 id가 반환된다"
#
#     @override
#     def given(self) -> Given[SeedingSession, AVariantAndACaller]:
#         return AVariantWithAPresetAndSomeone(role=UserRole.SUPERADMIN)
#
#     @override
#     def when(self) -> When[AVariantAndACaller, RuntimeVariantAdapter, DeleteRuntimeVariantPayload]:
#         return Deleting()
#
#     @override
#     def then(self) -> Then[AVariantAndACaller, DeleteRuntimeVariantPayload]:
#         return TheDeletedVariantId()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAVariant(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
    EnforcementOffLetsAnyoneDelete(),
    ManyAreDeletedAtOnce(started=datetime.now(UTC)),
    AnUnknownIdInTheListFailsAlone(started=datetime.now(UTC)),
    AUserGrantedNothingHasEveryVariantRefused(),
    # AVariantWithAPresetGoesWithIt(),  # TODO(BA-7931)
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
