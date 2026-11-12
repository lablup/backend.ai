"""시스템 세션 환경변수 하나 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    UpdateSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    SystemSessionEnvironNode,
    UpdateSystemSessionEnvironPayload,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.system_session_environ import (
    SystemSessionEnvironDeleted,
    SystemSessionEnvironKeyConflict,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.system_session_environ import (
    OTHER_KEY,
    ADeletedEnvironAndSomeone,
    AnEnvironAndACaller,
    AnEnvironAndSomeone,
    ManyEnvironsAndACaller,
    ManyEnvironsAndSomeone,
    TheEnvironNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED_KEY = "SCENARIO_EDITED_KEY"

type EditingStep = Scenario[
    TestSeedingSession, Any, SystemSessionEnvironAdapter, SystemSessionEnvironNode
]


@dataclass(frozen=True)
class Editing(When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]):
    key: str = EDITED_KEY

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AnEnvironAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.environ.key}의 이름을 {self.key}로 바꿉니다",
            english=f"{laid.caller.username} changes the key of {laid.environ.key} to {self.key}",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: AnEnvironAndACaller
    ) -> SystemSessionEnvironNode:
        with ActingAs(laid.caller):
            payload: UpdateSystemSessionEnvironPayload = await adapter.update(
                SystemSessionEnvironID(laid.environ.id),
                UpdateSystemSessionEnvironInput(key=self.key),
            )
        return payload.system_session_environ


@dataclass(frozen=True)
class AUserGrantedUpdateEdits(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-changes-the-key-of-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 수정 권한을 받은 사용자가 시스템 세션 환경변수의 이름을 바꾸면 새 이름과 이번 "
            "실행의 수정 시각을 실은 행 전체가 반환됩니다",
            english=(
                "when a user granted update permission in public changes a system session environ "
                "key, the whole row comes back with the new key and a last change time this run "
                "wrote"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Editing()

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheEnvironNode(written=self.started, key=EDITED_KEY)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 이름을 바꾸려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to change the key, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone()

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Editing()

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADuplicateKeyIsRefused(
    Scenario[
        TestSeedingSession,
        ManyEnvironsAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    @override
    def summary(self) -> str:
        return "editing-an-environ-to-a-key-another-row-holds-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "같은 범위에서 다른 행이 쓰는 이름으로 바꾸려 하면 거부됩니다",
            english=(
                "when a row is changed to a key another row already holds at the same scope, it "
                "is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyEnvironsAndACaller]:
        return ManyEnvironsAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[ManyEnvironsAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return EditingOneOfMany(key=OTHER_KEY)

    @override
    def then(self) -> Then[ManyEnvironsAndACaller, SystemSessionEnvironNode]:
        return TheCallIsRefused(SystemSessionEnvironKeyConflict)


@dataclass(frozen=True)
class EditingOneOfMany(
    When[ManyEnvironsAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]
):
    key: str

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ManyEnvironsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.laid[0].key}의 이름을 {self.key}로 바꿉니다",
            english=f"{laid.caller.username} changes the key of {laid.laid[0].key} to {self.key}",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: ManyEnvironsAndACaller
    ) -> SystemSessionEnvironNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(
                SystemSessionEnvironID(laid.laid[0].id),
                UpdateSystemSessionEnvironInput(key=self.key),
            )
        return payload.system_session_environ


@dataclass(frozen=True)
class ADeletedRowMayNotBeEdited(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    @override
    def summary(self) -> str:
        return "editing-a-deleted-environ-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "지운 행의 이름을 바꾸려 하면 먼저 복원하라는 이유로 거부됩니다",
            english=(
                "when the key of a soft-deleted row is changed, it is rejected with a demand to "
                "restore it first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return ADeletedEnvironAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Editing()

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheCallIsRefused(SystemSessionEnvironDeleted)


SCENARIOS: list[EditingStep] = [
    AUserGrantedUpdateEdits(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
    ADuplicateKeyIsRefused(),
    ADeletedRowMayNotBeEdited(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
