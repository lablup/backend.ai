"""allow_list 조회 — 개별 엔티티 권한 검사를 확인한다.

allow_list는 도메인·프로젝트·사용자 스코프에 자동 귀속되지 않는다. 따라서 현재 기본
역할로는 도달할 수 없으며, 슈퍼관리자만 조회할 수 있다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config_allow_list.response import (
    AppConfigAllowListNode,
)
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import (
    AppConfigAllowListAdapter,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.app_config import ENFORCEMENT
from bai_scenario.components.app_config_allow_list import (
    AnEntryAndACaller,
    AnEntryAndSomeone,
    TheEntryNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[
    TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
]


@dataclass(frozen=True)
class ReadingById(When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]):
    """ID로 조회한다. ID를 지정하지 않으면 준비한 allow_list의 ID를 쓴다."""

    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "admin_get"

    @override
    def describe(self, laid: AnEntryAndACaller) -> str:
        if self.other is not None:
            called_ko, called_en = "존재하지 않는 ID", "a missing ID"
        else:
            called_ko = f"{laid.name}의 allow_list"
            called_en = f"the allow_list of {laid.name}"
        return Says(
            f"{laid.caller.username}이 {called_ko} 조회합니다",
            english=f"{laid.caller.username} reads {called_en}",
        )

    @override
    async def call(
        self, adapter: AppConfigAllowListAdapter, laid: AnEntryAndACaller
    ) -> AppConfigAllowListNode:
        if self.other is not None:
            wanted = AppConfigAllowListID(self.other)
        elif laid.entry is not None:
            wanted = laid.entry.id
        else:
            raise LookupError("this row lays no entry to read")
        with ActingAs(laid.caller):
            return await adapter.admin_get(wanted)


@dataclass(frozen=True)
class TheSuperadminReadsIt(
    Scenario[
        TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-an-entry-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "allow_list 하나가 있고 superadmin 이 ID 로 조회하면, "
            "그 allow_list 의 모든 필드가 반환됩니다",
            english=(
                "with one allow_list laid, when the superadmin reads it by ID, "
                "every field of that allow_list comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheEntryNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[
        TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-an-entry"

    @override
    def describe(self) -> str:
        return Says(
            "같은 allow_list 를 권한이 없는 일반 사용자가 조회하면, "
            "엔티티 읽기 권한이 없어 거부됩니다",
            english=(
                "when a plain user without permission reads the same allow_list, "
                "the call is rejected because the user has no entity read permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownIdIsNotFoundForASuperadmin(
    Scenario[
        TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 ID 로 조회하면, 대상을 찾을 수 없다는 이유로 거부됩니다. "
            "권한 검사를 통과하는 사용자만 이 응답을 봅니다",
            english=(
                "when the superadmin reads a missing ID, the call is rejected because there "
                "is no such target. Only a user who passes the permission check sees this answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById(other=uuid4())

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneRead(
    Scenario[
        TestSeedingSession, AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode
    ],
    Configured,
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-plain-user-read"

    @override
    def describe(self) -> str:
        return Says(
            "RBAC 강제를 비활성화하면 권한이 없는 일반 사용자도 allow_list 를 조회할 수 있습니다",
            english=(
                "turning RBAC enforcement off lets a plain user without permission "
                "read an allow_list"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, AnEntryAndACaller]:
        return AnEntryAndSomeone(opened=AppConfigScopeType.USER)

    @override
    def when(self) -> When[AnEntryAndACaller, AppConfigAllowListAdapter, AppConfigAllowListNode]:
        return ReadingById()

    @override
    def then(self) -> Then[AnEntryAndACaller, AppConfigAllowListNode]:
        return TheEntryNode(started=self.started)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    AnUnknownIdIsNotFoundForASuperadmin(),
    EnforcementOffLetsAnyoneRead(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: AppConfigAllowListAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
