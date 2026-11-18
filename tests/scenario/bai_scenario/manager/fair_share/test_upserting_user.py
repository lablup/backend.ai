"""사용자 fair share 가중치 정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.request import UpsertUserFairShareWeightInput
from ai.backend.common.dto.manager.v2.fair_share.response import UserFairShareNode
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    WEIGHT,
    TheUserWeight,
    UsersInAGroupAndACaller,
    UsersInAGroupAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Upserted = UserFairShareNode
type FairShareStep = Scenario[TestSeedingSession, UsersInAGroupAndACaller, FairShareAdapter, Any]


@dataclass(frozen=True)
class Setting(When[UsersInAGroupAndACaller, FairShareAdapter, Upserted]):
    """그룹 안 사용자의 가중치를 정한다."""

    @override
    def operation(self) -> str:
        return "upsert_user"

    @override
    def describe(self, laid: UsersInAGroupAndACaller) -> str:
        return Says(
            (f"{laid.caller.username} 이 {laid.group.name} 안 첫 사용자의 가중치를 정합니다"),
            english=f"{laid.caller.username} sets the weight of the first user in {laid.group.name}",
        )

    @override
    async def call(self, adapter: FairShareAdapter, laid: UsersInAGroupAndACaller) -> Upserted:
        with ActingAs(laid.caller):
            payload = await adapter.upsert_user(
                UpsertUserFairShareWeightInput(
                    resource_group_name=laid.group.name,
                    user_uuid=laid.users[0].uuid,
                    project_id=laid.project.id,
                    domain_name=laid.domain.name,
                    weight=WEIGHT,
                )
            )
        return payload.user_fair_share


@dataclass(frozen=True)
class TheSuperadminSets(
    Scenario[TestSeedingSession, UsersInAGroupAndACaller, FairShareAdapter, Upserted]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-sets-a-user-weight"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그룹 안 사용자의 가중치를 정하면 그 가중치를 담은 기록이 오고 나머지 설정은 그룹 기본값입니다",
            english="when the superadmin sets the weight of a user in the group, the record comes back carrying that weight and the rest of the settings are the group defaults",
        )

    @override
    def given(self) -> Given[TestSeedingSession, UsersInAGroupAndACaller]:
        return UsersInAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[UsersInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[UsersInAGroupAndACaller, Upserted]:
        return TheUserWeight(started=self.started)


@dataclass(frozen=True)
class AUserGrantedUpdateOnTheGroupMayNotSet(
    Scenario[TestSeedingSession, UsersInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-may-not-set-a-user-weight"

    @override
    def describe(self) -> str:
        return Says(
            "그 그룹에 부여한 역할로 수정 권한을 받은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다. 가중치 쓰기는 그룹이 아니라 전역 대상을 기준으로 권한을 검사합니다",
            english="when a user granted the update permission through a role assigned on the group tries to set the weight of a user, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group",
        )

    @override
    def given(self) -> Given[TestSeedingSession, UsersInAGroupAndACaller]:
        return UsersInAGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[UsersInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[UsersInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSet(
    Scenario[TestSeedingSession, UsersInAGroupAndACaller, FairShareAdapter, Upserted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-set-a-user-weight"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 사용자의 가중치를 정하려 하면 권한 부족으로 거부됩니다",
            english="when a user granted nothing tries to set the weight of a user, it is rejected for a lack of permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, UsersInAGroupAndACaller]:
        return UsersInAGroupAndSomeone()

    @override
    def when(self) -> When[UsersInAGroupAndACaller, FairShareAdapter, Upserted]:
        return Setting()

    @override
    def then(self) -> Then[UsersInAGroupAndACaller, Upserted]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FairShareStep] = [
    TheSuperadminSets(started=datetime.now(UTC)),
    AUserGrantedUpdateOnTheGroupMayNotSet(),
    AUserGrantedNothingMayNotSet(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_upserting_users(
    scenario: FairShareStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
