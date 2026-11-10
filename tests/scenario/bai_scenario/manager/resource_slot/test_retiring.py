"""슬롯 종류 삭제 — id로 지정해 누가 삭제할 수 있고, 무엇이 아직 참조하면 거부되는가.

에이전트 자원, 모델 카드, 배포 preset이 아직 참조해서 거부되는 시나리오는 여기 없다. 그 셋을
미리 만들어 두는 seed가 아직 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import PurgeResourceSlotTypePayload
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeInUse
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation import (
    ASlotTypeAKernelAsksForAndSomeone,
    ASlotTypeARevisionUsesAndSomeone,
)
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheDeletedSlotName,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN = ResourceSlotTypeUUID(UUID("00000000-0000-0000-0000-0000000000ff"))

type Purged = PurgeResourceSlotTypePayload
type RetiringStep = Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]


@dataclass(frozen=True)
class Purging(When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]):
    """미리 만들어 둔 슬롯 종류를 id로 지정해 삭제한다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "purge_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        target_ko = "존재하지 않는 id" if self.unknown else laid.slot_type.slot_name
        target_en = "an id nothing answers to" if self.unknown else laid.slot_type.slot_name
        return Says(
            f"{laid.caller.username} 이 {target_ko} 를 영구 삭제합니다",
            english=f"{laid.caller.username} purges {target_en}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.purge_slot_type(UNKNOWN if self.unknown else laid.slot_type.uuid)


@dataclass(frozen=True)
class TheSuperadminPurgesASlotType(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-a-slot-type-nothing-refers-to"

    @override
    def describe(self) -> str:
        return Says(
            "아무것도 참조하지 않는 자원 슬롯 유형을 superadmin 이 id 로 영구 삭제하면 삭제한 "
            "이름을 담은 응답이 반환됩니다",
            english=(
                "when the superadmin purges a slot type nothing refers to by its id, the answer "
                "carries the name that was deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheDeletedSlotName()


@dataclass(frozen=True)
class ASlotAKernelStillAsksForMayNotBePurged(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-slot-type-a-kernel-still-asks-for-may-not-be-purged"

    @override
    def describe(self) -> str:
        return Says(
            "커널이 아직 할당받은 자원 슬롯 유형을 superadmin 이 영구 삭제하면 아직 사용 중이라는 "
            "이유로 거부됩니다",
            english=(
                "when the superadmin purges a slot type a kernel still holds an allocation for, "
                "the call is rejected because the slot type is still in use"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAKernelAsksForAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(ResourceSlotTypeInUse)


@dataclass(frozen=True)
class ASlotARevisionStillUsesMayNotBePurged(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-slot-type-a-deployment-revision-still-uses-may-not-be-purged"

    @override
    def describe(self) -> str:
        return Says(
            "배포 리비전이 아직 사용하는 자원 슬롯 유형을 superadmin 이 영구 삭제하면 아직 사용 "
            "중이라는 이유로 거부됩니다",
            english=(
                "when the superadmin purges a slot type a deployment revision still uses, the "
                "call is rejected because the slot type is still in use"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeARevisionUsesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(ResourceSlotTypeInUse)


@dataclass(frozen=True)
class AnIdNothingAnswersToIsNotFound(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "purging-a-slot-type-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 id 를 영구 삭제하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin purges an id nothing answers to, the call is rejected as "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 슬롯 유형을 영구 삭제하면 권한 부족으로 거부됩니다. "
            "수정이 역할 부족으로 거부되는 것과는 다른 검사입니다",
            english=(
                "when a user granted nothing purges a slot type, the call is rejected for lack "
                "of permission. This is a different check from the one that rejects an edit for "
                "lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingPurgingAnUnknownIdIsRefusedByPermission(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purging-an-unknown-slot-type-id-is-refused-by-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 존재하지 않는 id 를 영구 삭제하면 대상 없음이 아니라 권한 "
            "부족으로 거부됩니다. 호출한 사용자가 쓸 수 있는지를 대상을 찾기 전에 검사하기 "
            "때문입니다",
            english=(
                "when a user granted nothing purges an id nothing answers to, the call is "
                "rejected for lack of permission, not as not found, because whether the caller "
                "can use it is checked before the target is found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging(unknown=True)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyonePurge(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, Purged], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-purge-a-slot-type"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 자원 슬롯 유형을 영구 삭제할 수 있습니다",
            english=("turning permission checks off lets a user granted nothing purge a slot type"),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, Purged]:
        return Purging()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, Purged]:
        return TheDeletedSlotName()


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesASlotType(),
    ASlotAKernelStillAsksForMayNotBePurged(),
    ASlotARevisionStillUsesMayNotBePurged(),
    AnIdNothingAnswersToIsNotFound(),
    AUserGrantedNothingMayNotPurge(),
    AUserGrantedNothingPurgingAnUnknownIdIsRefusedByPermission(),
    EnforcementOffLetsAnyonePurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
