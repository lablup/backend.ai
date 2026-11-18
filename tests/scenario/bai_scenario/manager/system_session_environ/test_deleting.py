"""시스템 세션 환경변수 지우기와 되살리기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    SystemSessionEnvironNode,
)
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.system_session_environ import (
    ADeletedEnvironAndSomeone,
    AnEnvironAndACaller,
    AnEnvironAndSomeone,
    TheRowIsDeleted,
    TheRowIsRestored,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type DeletingStep = Scenario[
    TestSeedingSession, AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode
]


@dataclass(frozen=True)
class Deleting(When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]):
    operation_name: str = "delete"

    @override
    def operation(self) -> str:
        return self.operation_name

    @override
    def describe(self, laid: AnEnvironAndACaller) -> str:
        verb_ko = "되살립니다" if self.operation_name == "restore" else "지웁니다"
        verb_en = "restores" if self.operation_name == "restore" else "deletes"
        return Says(
            f"{laid.caller.username}이 {laid.environ.key}를 {verb_ko}",
            english=f"{laid.caller.username} {verb_en} {laid.environ.key}",
        )

    @override
    async def call(
        self, adapter: SystemSessionEnvironAdapter, laid: AnEnvironAndACaller
    ) -> SystemSessionEnvironNode:
        environ_id = SystemSessionEnvironID(laid.environ.id)
        with ActingAs(laid.caller):
            if self.operation_name == "restore":
                restored = await adapter.restore(environ_id)
                return restored.system_session_environ
            deleted = await adapter.delete(environ_id)
            return deleted.system_session_environ


@dataclass(frozen=True)
class AUserGrantedDeleteDeletes(
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
        return "a-user-granted-delete-deletes-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 삭제 권한을 받은 사용자가 시스템 세션 환경변수를 지우면 지운 시각을 실은 행 "
            "전체가 반환됩니다",
            english=(
                "when a user granted delete permission in public deletes a system session "
                "environ, the whole row comes back with the deletion time"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone(granted=(Permission.SOFT_DELETE,))

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Deleting()

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheRowIsDeleted(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 지우려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to delete a system session environ, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return AnEnvironAndSomeone()

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Deleting()

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedDeleteRestores(
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
        return "a-user-granted-delete-restores-a-deleted-environ"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 삭제 권한을 받은 사용자가 지운 시스템 세션 환경변수를 되살리면 지운 시각이 "
            "비워진 행 전체가 반환됩니다",
            english=(
                "when a user granted delete permission in public restores a deleted system session "
                "environ, the whole row comes back with no deletion time"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return ADeletedEnvironAndSomeone(granted=(Permission.SOFT_DELETE,))

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Deleting(operation_name="restore")

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheRowIsRestored(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[
        TestSeedingSession,
        AnEnvironAndACaller,
        SystemSessionEnvironAdapter,
        SystemSessionEnvironNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-an-environ"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 되살리려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to restore a system session environ, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnEnvironAndACaller]:
        return ADeletedEnvironAndSomeone()

    @override
    def when(
        self,
    ) -> When[AnEnvironAndACaller, SystemSessionEnvironAdapter, SystemSessionEnvironNode]:
        return Deleting(operation_name="restore")

    @override
    def then(self) -> Then[AnEnvironAndACaller, SystemSessionEnvironNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DeletingStep] = [
    AUserGrantedDeleteDeletes(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotDelete(),
    AUserGrantedDeleteRestores(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRestore(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_deleting(
    scenario: DeletingStep,
    adapter: SystemSessionEnvironAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
