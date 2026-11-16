"""프리셋 하나와 여럿을 id 로 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.role_preset import (
    APresetAndACaller,
    APresetAndSomeone,
    EveryEntryIsDenied,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    TheWholePreset,
    TheWholePresetsInOrder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

ROLE_TEMPLATE = "team-member"
"""The template the row lays, so no optional field is left at its default."""

type Loaded = list[RolePresetNode | Exception | None]
type ReadingStep = Scenario[
    TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode
]
type LoadingStep = Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Loaded]


@dataclass(frozen=True)
class Reading(When[APresetAndACaller, RolePresetAdapter, RolePresetNode]):
    """미리 만들어 둔 프리셋을 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APresetAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.preset.name}을 id 로 조회합니다",
            english=f"{laid.caller.username} reads {laid.preset.name} by id",
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: APresetAndACaller) -> RolePresetNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.preset.id)


@dataclass(frozen=True)
class Loading(When[ManyPresetsAndACaller, RolePresetAdapter, Loaded]):
    """미리 만들어 둔 프리셋들의 id 를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 프리셋 {len(laid.laid)}개의 id 를 한 번에 "
            "조회합니다",
            english=(
                f"{laid.caller.username} reads the ids of {len(laid.laid)} presets seeded in "
                "advance at once"
            ),
        )

    @override
    async def call(self, adapter: RolePresetAdapter, laid: ManyPresetsAndACaller) -> Loaded:
        ids = [one.id for one in laid.laid]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class AGrantedUserReadsIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-a-preset-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 조회 권한을 받은 사용자가 id 로 조회하면, 미리 저장한 프리셋 전체가 "
            "반환됩니다",
            english=(
                "when a user granted read in global reads by id, the whole preset seeded in "
                "advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone(
            granted=Permission.READ,
            auto_assign=True,
            auto_assign_to_owner=True,
            role_name_template=ROLE_TEMPLATE,
        )

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Reading()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheWholePreset()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadIt(
    Scenario[TestSeedingSession, APresetAndACaller, RolePresetAdapter, RolePresetNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 id 로 조회하려 하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read by id, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APresetAndACaller]:
        return APresetAndSomeone()

    @override
    def when(self) -> When[APresetAndACaller, RolePresetAdapter, RolePresetNode]:
        return Reading()

    @override
    def then(self) -> Then[APresetAndACaller, RolePresetNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserReadsManyInOrder(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-many-presets-in-order"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 조회 권한을 받은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 둘 다 "
            "요청한 순서대로 각각 전체가 반환됩니다",
            english=(
                "when a user granted read in global loads the ids of two presets at once, both "
                "come back whole in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return TheWholePresetsInOrder()


@dataclass(frozen=True)
class AUserGrantedNothingLoadsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RolePresetAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-many-presets-is-denied-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 둘의 id 를 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads the ids of two presets at once, instead of "
                "the whole request being rejected, every entry comes back holding a rejection "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RolePresetAdapter, Loaded]:
        return Loading()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Loaded]:
        return EveryEntryIsDenied()


SCENARIOS: list[ReadingStep | LoadingStep] = [
    AGrantedUserReadsIt(),
    AUserGrantedNothingMayNotReadIt(),
    AGrantedUserReadsManyInOrder(),
    AUserGrantedNothingLoadsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep | LoadingStep,
    adapter: RolePresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
