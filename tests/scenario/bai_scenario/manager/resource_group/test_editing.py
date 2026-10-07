"""리소스 그룹 수정 — 수정과 설정 수정은 같은 검사를 거치고, 바꿀 수 있는 필드의 범위만 다르다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    PreemptionConfigInputDTO,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import ResourceGroupDetailNode
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    SchedulerTypeDTO,
)
from ai.backend.common.types import PreemptionOrder, PreemptionVictimScope
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DefaultResourceGroupAlreadyExists
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    AGroupBesideTheDefaultAndSomeone,
    GroupLook,
    TheGroupNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingStep = Scenario[
    SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode
]

UNKNOWN = "no-such-group"
DESCRIBED = "moved to the second rack"
PROXY = "https://proxy.example.test"


@dataclass(frozen=True)
class Editing(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """지정한 필드만 바꾼다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    described: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target = "존재하지 않는 이름" if self.unknown else laid.group.name
        changes: list[str] = []
        if self.described is not None:
            changes.append("설명을 새것으로")
        if self.is_active is not None:
            changes.append(f"활성을 {self.is_active}로")
        if self.is_default is not None:
            changes.append(f"기본을 {self.is_default}로")
        what = ", ".join(changes) if changes else "아무것도 지정하지 않고"
        return f"{laid.caller.username}이 {target}을 {what} 수정"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        fields: dict[str, Any] = {}
        if self.described is not None:
            fields["description"] = self.described
        if self.is_active is not None:
            fields["is_active"] = self.is_active
        if self.is_default is not None:
            fields["is_default"] = self.is_default
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UNKNOWN if self.unknown else laid.group.name, UpdateResourceGroupInput(**fields)
            )
        return payload.resource_group


@dataclass(frozen=True)
class EditingTheConfig(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """설정을 바꾼다. ``preemption``이면 선점 설정을, 아니면 스케줄러·공개·네트워크를 바꾼다."""

    preemption: bool = False

    @override
    def operation(self) -> str:
        return "update_config"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        what = "선점 설정을" if self.preemption else "스케줄러·공개·네트워크 설정을"
        return f"{laid.caller.username}이 {laid.group.name}의 {what} 수정"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        if self.preemption:
            asked = UpdateResourceGroupConfigInput(
                resource_group_name=laid.group.name,
                preemption=PreemptionConfigInputDTO(
                    enabled=True,
                    preemptible_priority=3,
                    order=PreemptionOrder.NEWEST.value,
                    mode=PreemptionModeDTO.RESCHEDULE.value,
                    preemption_min_runtime=60,
                    victim_scope=PreemptionVictimScope.PROJECT,
                ),
            )
        else:
            asked = UpdateResourceGroupConfigInput(
                resource_group_name=laid.group.name,
                scheduler_type=SchedulerTypeDTO.LIFO,
                is_public=False,
                use_host_network=True,
                app_proxy_addr=PROXY,
            )
        with ActingAs(laid.caller):
            payload = await adapter.update_config(asked)
        return payload.resource_group


@dataclass(frozen=True)
class TheSuperadminChangesTheDescription(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changing-the-description-leaves-the-rest"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 설명만 바꾸면 설명은 새 값이고 나머지는 그대로인 그룹 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(described=DESCRIBED)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started, described=DESCRIBED))


@dataclass(frozen=True)
class DeactivatingAGroup(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "deactivating-a-resource-group-answers-it-inactive"

    @override
    def describe(self) -> str:
        return "활성 그룹을 비활성으로 바꾸면 비활성인 그룹이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(is_active=False)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started, is_active=False))


@dataclass(frozen=True)
class MakingAGroupTheDefault(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "making-a-resource-group-the-default-answers-it-default"

    @override
    def describe(self) -> str:
        return "기본 그룹이 없을 때 그룹을 기본으로 바꾸면 기본인 그룹이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(is_default=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started, is_default=True))


@dataclass(frozen=True)
class ASecondDefaultIsRefused(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "making-a-second-resource-group-the-default-is-refused"

    @override
    def describe(self) -> str:
        return "기본 그룹이 따로 있을 때 다른 그룹을 기본으로 바꾸려 하면 기본 그룹이 이미 있다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupBesideTheDefaultAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(is_default=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(DefaultResourceGroupAlreadyExists)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-naming-no-field-changes-nothing"

    @override
    def describe(self) -> str:
        return "아무 필드도 지정하지 않고 수정하면 아무것도 바뀌지 않은 그룹이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupEditsIt(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-changes-its-description"

    @override
    def describe(self) -> str:
        return "그 그룹에 앉힌 역할로 수정 권한을 받은 사용자가 설명을 바꾸면 설명이 새 값인 그룹이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(described=DESCRIBED)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started, described=DESCRIBED))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-resource-group"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 설명을 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(described=DESCRIBED)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminEditingAnUnknownNameIsNotFound(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-editing-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 이름을 수정하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return Editing(described=DESCRIBED, unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminChangesTheConfig(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-scheduler-visibility-and-network-config"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 스케줄러를 후입선출로, 비공개로, 호스트 네트워크로, 프록시 주소를 지정해 "
            "설정을 바꾸면 그 값들이 새 값인 그룹 전체가 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheConfig()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(
            GroupLook(
                started=self.started,
                scheduler_type=SchedulerTypeDTO.LIFO,
                is_public=False,
                use_host_network=True,
                wsproxy_addr=PROXY,
            )
        )


@dataclass(frozen=True)
class TheSuperadminChangesThePreemptionConfig(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-changes-the-preemption-config"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 선점 설정을 바꾸면 선점 설정이 새 값인 그룹 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheConfig(preemption=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(
            GroupLook(
                started=self.started,
                preemption_enabled=True,
                preemptible_priority=3,
                preemption_order=PreemptionOrder.NEWEST,
                preemption_mode=PreemptionModeDTO.RESCHEDULE,
                preemption_min_runtime=60.0,
                victim_scope=PreemptionVictimScope.PROJECT,
            )
        )


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEditTheConfig(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-the-config"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 설정을 바꾸려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return EditingTheConfig()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[EditingStep] = [
    TheSuperadminChangesTheDescription(started=datetime.now(UTC)),
    DeactivatingAGroup(started=datetime.now(UTC)),
    MakingAGroupTheDefault(started=datetime.now(UTC)),
    ASecondDefaultIsRefused(),
    AnEmptyEditChangesNothing(started=datetime.now(UTC)),
    AUserGrantedUpdateOnTheGroupEditsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    TheSuperadminEditingAnUnknownNameIsNotFound(),
    TheSuperadminChangesTheConfig(started=datetime.now(UTC)),
    TheSuperadminChangesThePreemptionConfig(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEditTheConfig(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
