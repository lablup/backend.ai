"""프리셋 삭제 — 누가 삭제할 수 있는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

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
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.runtime_variant_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    TheDeletedPresetId,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = DeleteRuntimeVariantPresetPayload
type RetiringStep = Scenario[
    TestSeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted
]


@dataclass(frozen=True)
class Deleting(When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]):
    """미리 만들어 둔 프리셋 하나를 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        target = "존재하지 않는 ID" if self.unknown else laid.preset.name
        target_en = "an unknown id" if self.unknown else laid.preset.name
        return Says(
            f"{laid.caller.username}의 삭제 요청: 대상: {target}",
            english=f"delete request from {laid.caller.username}: target: {target_en}",
        )

    @override
    async def call(self, adapter: RuntimeVariantPresetAdapter, laid: APresetAndACaller) -> Deleted:
        with ActingAs(laid.caller):
            return await adapter.purge(uuid4() if self.unknown else laid.preset.id)


@dataclass(frozen=True)
class TheSuperadminDeletesAPreset(
    Scenario[TestSeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-deletes-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 런타임 파라미터를 삭제하면 삭제한 런타임 파라미터의 ID 를 담은 응답이 "
            "반환됩니다",
            english=(
                "when the superadmin deletes a preset, a response carrying the id of the deleted "
                "preset comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheDeletedPresetId()


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "deleting-a-preset-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 ID 를 삭제하면 대상을 찾을 수 없어 요청이 거부됩니다",
            english=(
                "when the superadmin deletes an unknown id, the request is rejected because the "
                "target cannot be found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting(unknown=True)

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[TestSeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 런타임 파라미터를 삭제하면 권한이 부족하여 요청이 "
            "거부됩니다",
            english=(
                "when a user granted nothing deletes a preset, the request is rejected for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RuntimeVariantPresetAdapter, Deleted]:
        return Deleting()

    @override
    def then(self) -> Then[APresetAndACaller, Deleted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneDelete(
    Scenario[TestSeedingSession, APresetAndACaller, RuntimeVariantPresetAdapter, Deleted],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-delete-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 런타임 파라미터를 삭제할 수 있습니다",
            english=(
                "turning the permission check off lets even a user granted nothing delete a preset"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
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
