"""fair share 설정 — 읽기는 전체 검색을 거쳐 슈퍼관리자 검사를 받고, 수정은 그룹을 지목하는 권한 검사만 받는다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    UpdateResourceGroupFairShareSpecInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    FairShareResourceGroupSpecInfo,
    ResourceGroupDetailNode,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    GroupLook,
    TheFairShareDefaults,
    TheGroupNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type FairShareStep = Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, Any]

UNKNOWN = "no-such-group"
HALF_LIFE = 14


@dataclass(frozen=True)
class ReadingTheSpec(When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]):
    """fair share 설정을 읽는다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_fair_share_spec"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target = "존재하지 않는 이름" if self.unknown else laid.group.name
        return f"{laid.caller.username}이 {target}의 fair share 설정 조회"

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
        target = "존재하지 않는 이름" if self.unknown else laid.group.name
        return f"{laid.caller.username}이 {target}의 fair share 설정에서 반감기를 수정"

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
class TheSuperadminReadsTheDefaults(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-default-fair-share-spec"

    @override
    def describe(self) -> str:
        return (
            "에이전트가 없는 그룹의 fair share 설정을 슈퍼관리자가 읽으면 "
            "코드가 정한 기본값이 반환되고 가중치 목록은 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheFairShareDefaults()


@dataclass(frozen=True)
class AUserGrantedReadOnTheGroupReadsTheSpec(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-its-fair-share-spec"

    @override
    def describe(self) -> str:
        return (
            "그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 에이전트 없는 그룹의 fair share 설정을 "
            "읽으면 코드가 정한 기본값이 반환되고 가중치 목록은 비어 있다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheFairShareDefaults()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheSpec(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-fair-share-spec"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 fair share 설정을 읽으려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReadingTheSpecOfAnUnknownNameIsNotFound(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]
):
    @override
    def summary(self) -> str:
        return "reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 이름의 fair share 설정을 읽으면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, FairShareResourceGroupSpecInfo]:
        return ReadingTheSpec(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminChangesTheHalfLife(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-fair-share-half-life"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 반감기를 바꾸면 그룹 전체가 반환된다. 반환되는 노드에는 이 설정이 실리지 않는다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupChangesTheSpec(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-changes-its-fair-share-spec"

    @override
    def describe(self) -> str:
        return (
            "그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 반감기를 바꾸면 그룹 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeTheSpec(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-the-fair-share-spec"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 반감기를 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ChangingTheSpecOfAnUnknownNameIsNotFound(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 이름의 반감기를 바꾸면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheSpec(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminReadsTheDefaults(),
    AUserGrantedReadOnTheGroupReadsTheSpec(),
    AUserGrantedNothingMayNotReadTheSpec(),
    ReadingTheSpecOfAnUnknownNameIsNotFound(),
    TheSuperadminChangesTheHalfLife(started=datetime.now(UTC)),
    AUserGrantedUpdateOnTheGroupChangesTheSpec(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotChangeTheSpec(),
    ChangingTheSpecOfAnUnknownNameIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_fair_share(
    scenario: FairShareStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
