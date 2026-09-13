"""보존 정책 조회 — 다른 카탈로그와 달리 하나를 조회하는 것도 권한 검사를 거친다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    APolicyAndACaller,
    APolicyAndSomeone,
    ThePolicyNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.retention_policy import RetentionPolicyID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.response import RetentionPolicyNode
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type ReadingStep = Scenario[
    SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode
]


@dataclass(frozen=True)
class ReadingById(When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]):
    """id로 조회한다. ``unknown``이면 어느 행에도 없는 id를 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: APolicyAndACaller) -> str:
        target = (
            "존재하지 않는 id" if self.unknown else f"{laid.policy.category.value} 카테고리 정책"
        )
        return f"{laid.caller.username}이 {target} 조회"

    @override
    async def call(
        self, adapter: RetentionPolicyAdapter, laid: APolicyAndACaller
    ) -> RetentionPolicyNode:
        with ActingAs(laid.caller):
            return await adapter.get(RetentionPolicyID(uuid4()) if self.unknown else laid.policy.id)


@dataclass(frozen=True)
class TheSuperadminReadsAPolicy(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-policy-by-id"

    @override
    def describe(self) -> str:
        return "정책 하나가 있고 슈퍼관리자가 id로 조회하면, 그 정책 전체가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-policy"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 id로 조회하면 권한 부족으로 거부된다. "
            "인증만으로 조회되는 다른 카탈로그와 달리 이 조회는 권한 검사를 거친다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownIdIsNotFound(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 id로 조회하면 대상 없음이 아니라 권한 부족으로 "
            "거부된다. 권한 검사가 먼저 실행되고 없는 행에는 부여된 권한도 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById(unknown=True)

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRead(
    Scenario[SeedingSession, APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-read-a-policy"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 정책을 조회할 수 있다. "
            "조회는 역할이 아니라 권한 그래프로 보호되기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APolicyAndACaller]:
        return APolicyAndSomeone()

    @override
    def when(self) -> When[APolicyAndACaller, RetentionPolicyAdapter, RetentionPolicyNode]:
        return ReadingById()

    @override
    def then(self) -> Then[APolicyAndACaller, RetentionPolicyNode]:
        return ThePolicyNode(started=self.started)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsAPolicy(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheSuperadminReadingAnUnknownIdIsNotFound(),
    AUserGrantedNothingReadingAnUnknownIdIsRefusedForPermission(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
