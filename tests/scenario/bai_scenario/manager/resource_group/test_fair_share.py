"""fair share 설정 — 읽기는 전체 검색을 거쳐 슈퍼관리자 검사를 받고, 수정은 그룹을 지목하는 권한 검사만 받는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceWeightEntryInput,
    UpdateResourceGroupFairShareSpecInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    FairShareResourceGroupSpecInfo,
    ResourceGroupDetailNode,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.fair_share import InvalidResourceWeightError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    GroupLook,
    TheFairShareDefaults,
    TheGroupNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type FairShareStep = Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Any]

UNKNOWN = "no-such-group"
ABSENT_RESOURCE = "no-such-slot"
HALF_LIFE = 14
WEIGHT = Decimal("2")


@dataclass(frozen=True)
class ReadingTheSpec(When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]):
    """fair share 설정을 읽는다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_fair_share_spec"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target_ko = "존재하지 않는 이름" if self.unknown else laid.group.name
        target_en = "a name that does not exist" if self.unknown else laid.group.name
        return Says(
            f"{laid.caller.username}이 {target_ko}의 fair share 설정을 조회합니다",
            english=f"{laid.caller.username} reads the fair share config of {target_en}",
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> FairShareResourceGroupSpecInfo:
        with ActingAs(laid.caller):
            return await adapter.get_fair_share_spec(UNKNOWN if self.unknown else laid.group.name)


@dataclass(frozen=True)
class EditingTheSpec(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """fair share 설정의 반감기를 바꾼다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update_fair_share_spec"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target_ko = "존재하지 않는 이름" if self.unknown else laid.group.name
        target_en = "a name that does not exist" if self.unknown else laid.group.name
        return Says(
            f"{laid.caller.username}이 {target_ko}의 fair share 설정에서 반감기를 수정합니다",
            english=(
                f"{laid.caller.username} changes the half-life in the fair share config of "
                f"{target_en}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        asked = UpdateResourceGroupFairShareSpecInput(
            resource_group_name=UNKNOWN if self.unknown else laid.group.name,
            half_life_days=HALF_LIFE,
        )
        with ActingAs(laid.caller):
            payload = await adapter.update_fair_share_spec(asked)
        return payload.resource_group


@dataclass(frozen=True)
class AssigningAResourceWeight(
    When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    """슬롯 종류 하나에 가중치를 지정한다. ``absent``면 보고된 적 없는 이름에 지정한다."""

    absent: bool = False

    @override
    def operation(self) -> str:
        return "update_fair_share_spec"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        named = ABSENT_RESOURCE if self.absent else laid.slot_name
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 {named} 가중치를 지정합니다",
            english=(f"{laid.caller.username} assigns a weight to {named} on {laid.group.name}"),
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        named = ABSENT_RESOURCE if self.absent else laid.slot_name
        asked = UpdateResourceGroupFairShareSpecInput(
            resource_group_name=laid.group.name,
            resource_weights=[ResourceWeightEntryInput(resource_type=named, weight=WEIGHT)],
        )
        with ActingAs(laid.caller):
            payload = await adapter.update_fair_share_spec(asked)
        return payload.resource_group


@dataclass(frozen=True)
class TheSuperadminReadsTheDefaults(
    Scenario[
        TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-default-fair-share-spec"

    @override
    def describe(self) -> str:
        return Says(
            "에이전트가 없는 자원 그룹의 fair share 설정을 superadmin 이 읽으면 코드가 정한 "
            "기본값이 반환되고 가중치 목록은 비어 있습니다",
            english=(
                "when the superadmin reads the fair share config of a resource group with no "
                "agent, the defaults set in the code come back and the weight list is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheFairShareDefaults()


@dataclass(frozen=True)
class AUserGrantedReadOnTheGroupReadsTheSpec(
    Scenario[
        TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-its-fair-share-spec"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 읽기 권한을 받은 사용자가 에이전트 없는 자원 그룹의 "
            "fair share 설정을 읽으면 코드가 정한 기본값이 반환되고 가중치 목록은 비어 있습니다",
            english=(
                "a user granted read through the role granted on the resource group reading the "
                "fair share config of a resource group with no agent gets the defaults set in "
                "the code and an empty weight list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheFairShareDefaults()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheSpec(
    Scenario[
        TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-fair-share-spec"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 fair share 설정을 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to read the fair share config is rejected for "
                "not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReadingTheSpecOfAnUnknownNameIsNotFound(
    Scenario[
        TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo
    ]
):
    @override
    def summary(self) -> str:
        return "reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름의 fair share 설정을 읽으면 대상을 찾을 수 없다는 "
            "이유로 거부됩니다",
            english=(
                "when the superadmin reads the fair share config of a name nothing answers to, "
                "the call is rejected because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminChangesTheHalfLife(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-fair-share-half-life"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 반감기를 바꾸면 그룹 전체가 반환됩니다. 반환되는 노드에는 이 설정이 "
            "담기지 않습니다",
            english=(
                "when the superadmin changes the half-life, the whole group comes back. the "
                "returned node does not carry this config"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupChangesTheSpec(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-changes-its-fair-share-spec"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 수정 권한을 받은 사용자가 반감기를 바꾸면 그룹 전체가 "
            "반환됩니다",
            english=(
                "a user granted update through the role granted on the resource group changing "
                "the half-life gets the whole group"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeTheSpec(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-the-fair-share-spec"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 반감기를 바꾸려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to change the half-life is rejected for not "
                "enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ChangingTheSpecOfAnUnknownNameIsNotFound(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름의 반감기를 바꾸면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin changes the half-life of a name nothing answers to, the "
                "call is rejected because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminAssignsAResourceWeight(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-assigns-a-resource-weight"

    @override
    def describe(self) -> Says:
        return Says(
            "superadmin 이 슬롯 종류 하나의 가중치를 지정하면 그룹 전체가 반환됩니다. 반환되는 "
            "노드에는 이 설정이 담기지 않습니다",
            english=(
                "when the superadmin assigns a weight to one resource type, the whole group comes "
                "back. the returned node does not carry this config"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN, reports_a_slot=True)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return AssigningAResourceWeight()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AWeightOnAnUnreportedResourceIsRejected(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-weight-on-a-resource-no-agent-reports-is-rejected"

    @override
    def describe(self) -> Says:
        return Says(
            "에이전트가 보고하지 않은 슬롯 종류에 가중치를 지정하면 입력이 잘못되었다는 것으로 "
            "거부됩니다",
            english=(
                "assigning a weight to a resource type no agent reports is rejected as an invalid "
                "input"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return AssigningAResourceWeight(absent=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(InvalidResourceWeightError)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminReadsTheDefaults(),
    AUserGrantedReadOnTheGroupReadsTheSpec(),
    AUserGrantedNothingMayNotReadTheSpec(),
    ReadingTheSpecOfAnUnknownNameIsNotFound(),
    TheSuperadminChangesTheHalfLife(started=datetime.now(UTC)),
    TheSuperadminAssignsAResourceWeight(started=datetime.now(UTC)),
    AWeightOnAnUnreportedResourceIsRejected(),
    AUserGrantedUpdateOnTheGroupChangesTheSpec(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotChangeTheSpec(),
    ChangingTheSpecOfAnUnknownNameIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_fair_share(
    scenario: FairShareStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
