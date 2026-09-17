"""카테고리 삭제 — 누가 삭제할 수 있는가.

이 어댑터에는 soft delete가 없다. 정의가 참조하는 카테고리를 삭제하는 행은 아래에 주석으로
있다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    DeleteCategoryInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    DeleteCategoryPayload,
)
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset_category import (
    ACategoryAndACaller,
    ACategoryAndSomeone,
    TheRemovedOneIsNamed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

ENFORCEMENT = "manager.rbac.enforcement_enabled"

type Adapter = PrometheusQueryPresetCategoryAdapter
type Removed = DeleteCategoryPayload
type PurgingStep = Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed]


@dataclass(frozen=True)
class Removing(When[ACategoryAndACaller, Adapter, Removed]):
    """카테고리 하나를 삭제한다. id를 지정하지 않으면 미리 만들어 둔 카테고리를 삭제한다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: ACategoryAndACaller) -> str:
        called = "존재하지 않는 id" if self.other is not None else laid.category.name
        return f"{laid.caller.username}이 {called} 삭제"

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAndACaller) -> Removed:
        wanted = self.other if self.other is not None else laid.category.id
        with ActingAs(laid.caller):
            return await adapter.delete(DeleteCategoryInput(id=wanted))


@dataclass(frozen=True)
class TheSuperadminRemovesIt(Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed]):
    @override
    def summary(self) -> str:
        return "the-superadmin-removes-a-category"

    @override
    def describe(self) -> str:
        return "카테고리 하나가 있고 슈퍼관리자가 삭제하면, 삭제한 id를 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[ACategoryAndACaller, Removed]:
        return TheRemovedOneIsNamed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRemove(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-remove-a-category"

    @override
    def describe(self) -> str:
        return "같은 카테고리가 있고 아무 권한도 없는 사용자가 삭제하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[ACategoryAndACaller, Removed]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRemove(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-remove-a-category"

    @override
    def describe(self) -> str:
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 카테고리를 삭제할 수 있다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone()

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, Removed]:
        return Removing()

    @override
    def then(self) -> Then[ACategoryAndACaller, Removed]:
        return TheRemovedOneIsNamed()


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed]
):
    @override
    def summary(self) -> str:
        return "removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id를 삭제하면, 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
        return ACategoryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACategoryAndACaller, Adapter, Removed]:
        return Removing(other=uuid4())

    @override
    def then(self) -> Then[ACategoryAndACaller, Removed]:
        return TheCallIsRefused(EntityNotFoundError)


# TODO: 정의가 참조하는 카테고리를 삭제하면 거부되어야 하는데, 지금은 충돌 검사 없이 삭제되고
# 그 정의의 카테고리 필드가 비어서 이 행이 실패한다. 삭제가 거부되도록 고쳐지면 주석을 풀어
# SCENARIOS에 넣는다. 정의 seed(SeedPresetIn)는 prometheus_query_preset 시나리오가 들여오고,
# 거부 예외의 이름은 고칠 때 정한다.
#
# @dataclass(frozen=True)
# class AReferencedCategoryAndSomeone(Given[Any, ACategoryAndACaller]):
#     """카테고리 하나와 그것을 참조하는 정의 하나, 호출자 한 명."""
#
#     role: UserRole = UserRole.USER
#
#     @override
#     def describe(self) -> str:
#         return f"카테고리 하나와 그것을 참조하는 정의 하나, {self.role.value} 한 명"
#
#     @override
#     async def lay(self, seeding: Any) -> ACategoryAndACaller:
#         category = await seeding.creating(SeedCategory())
#         await seeding.creating_from(SeedPresetIn(), category)
#         caller = await lay_someone(seeding, self.role)
#         return ACategoryAndACaller(category=seeding.made(category), caller=seeding.made(caller))
#
#
# @dataclass(frozen=True)
# class AReferencedCategoryIsNotRemoved(
#     Scenario[SeedingSession, ACategoryAndACaller, Adapter, Removed]
# ):
#     @override
#     def summary(self) -> str:
#         return "a-category-a-preset-still-points-at-is-not-removed"
#
#     @override
#     def describe(self) -> str:
#         return "정의가 참조하는 카테고리를 슈퍼관리자가 삭제하면, 아직 참조 중이라는 이유로 거부된다"
#
#     @override
#     def given(self) -> Given[SeedingSession, ACategoryAndACaller]:
#         return AReferencedCategoryAndSomeone(role=UserRole.SUPERADMIN)
#
#     @override
#     def when(self) -> When[ACategoryAndACaller, Adapter, Removed]:
#         return Removing()
#
#     @override
#     def then(self) -> Then[ACategoryAndACaller, Removed]:
#         return TheCallIsRefused(PrometheusQueryPresetCategoryInUse)


SCENARIOS: list[PurgingStep] = [
    TheSuperadminRemovesIt(),
    AUserGrantedNothingMayNotRemove(),
    EnforcementOffLetsAnyoneRemove(),
    AnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: PurgingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
