"""슬롯 종류 삭제 — 이름으로 지정해 누가 삭제할 수 있고, 권한 검사를 끄면 무엇이 허용되는가.

아직 참조하는 곳이 있어 거부되는 다섯 시나리오는 여기 없다. 에이전트 자원, 커널 할당, 모델 카드,
배포 preset, 배포 리비전을 미리 만들어 두는 seed가 아직 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheDeletedSlotName,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.request import PurgeResourceSlotTypeInput
from ai.backend.common.dto.manager.v2.resource_slot.response import PurgeResourceSlotTypePayload
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

UNKNOWN = "no-such-slot"

type Purged = PurgeResourceSlotTypePayload
type RetiringStep = Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]


@dataclass(frozen=True)
class Purging(When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]):
    """미리 만들어 둔 슬롯 종류를 이름으로 지정해 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_purge_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        target = UNKNOWN if self.unknown else laid.slot_type.slot_name
        return f"{laid.caller.username}이 {target} 삭제"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.admin_purge_slot_type(
                PurgeResourceSlotTypeInput(
                    slot_name=UNKNOWN if self.unknown else laid.slot_type.slot_name
                )
            )


@dataclass(frozen=True)
class TheSuperadminPurgesASlotType(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-slot-type-nothing-refers-to"

    @override
    def describe(self) -> str:
        return "아무것도 참조하지 않는 슬롯 종류를 슈퍼관리자가 이름으로 삭제하면 삭제한 이름을 담은 응답이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheDeletedSlotName()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-a-slot-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 이름을 삭제하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-slot-type"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 슬롯 종류를 삭제하면 권한 부족으로 거부된다. "
            "수정이 역할 부족으로 거부되는 것과는 다른 검사다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingStillHearsNotFound(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purging-an-unknown-slot-name-hears-not-found"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 이름을 삭제하면 권한 부족이 아니라 대상 없음으로 거부된다. "
            "이름을 풀어내는 단계가 권한을 검사하지 않고 먼저 실행되기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffLetsAnyonePurge(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-purge-a-slot-type"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 슬롯 종류를 삭제할 수 있다. "
            "삭제는 수정과 달리 권한 그래프로 보호되므로 스위치가 영향을 준다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheDeletedSlotName()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesASlotType(),
    ANameNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotPurge(),
    AUserGrantedNothingStillHearsNotFound(),
    EnforcementOffLetsAnyonePurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
