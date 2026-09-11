"""preset 지우기 — 누가 지울 수 있고, 집행을 끄면 무엇이 열리는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    TheDeletedPresetId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    DeleteRuntimeVariantPresetPayload,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type Deleted = DeleteRuntimeVariantPresetPayload
type RetiringStep = Scenario[
    SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted
]


@dataclass(frozen=True)
class Deleting(When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]):
    """심은 preset 하나를 지운다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "delete"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "없는 id" if self.unknown else laid.preset.name
        return f"{laid.caller.username}이 {target}를 지움"

    @override
    async def call(self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.delete(uuid4() if self.unknown else laid.preset.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAPreset(
    Scenario[SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-preset"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 preset을 지우면 지운 preset의 id를 실은 답이 온다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheDeletedPresetId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-preset-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무 preset도 갖지 않은 id를 지우면 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-preset"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 preset을 지우면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[SeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-preset"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 preset을 지운다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheDeletedPresetId()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminDeletesAPreset(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotDelete(),
    EnforcementOffLetsAnyoneDelete(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
