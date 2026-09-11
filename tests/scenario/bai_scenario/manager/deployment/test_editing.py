"""배포 고치기 — 무엇이 바뀌고, 누가 바꿀 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import (
    ADeploymentAndACaller,
    ADeploymentInThatPlace,
    AnothersDeploymentAndASuperadmin,
    TheDeploymentNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import UpdateDeploymentInput
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

RENAMED = "renamed"
KEPT = "keep"

type EditingStep = Scenario[
    SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode
]


@dataclass(frozen=True)
class Editing(When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]):
    """배포 하나를 고친다. 대지 않은 자리는 그대로 둔다."""

    named: str | None = None
    replicas: int | None = None
    clearing_tags: bool = False
    opening: bool | None = None
    other: UUID | None = None

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        changed = []
        if self.named is not None:
            changed.append(f"이름을 {self.named}으로")
        if self.replicas is not None:
            changed.append(f"복제 수를 {self.replicas}으로")
        if self.clearing_tags:
            changed.append("태그를 비우도록")
        if self.opening is not None:
            changed.append("바깥에 열도록" if self.opening else "바깥에 닫도록")
        called = (
            "아무것도 갖지 않은 id" if self.other is not None else laid.deployment.metadata.name
        )
        return (
            f"{laid.caller.username}이 {called}를 {', '.join(changed) or '아무것도 대지 않고'} 수정"
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller) -> DeploymentNode:
        wanted = DeploymentID(self.other) if self.other is not None else laid.deployment.id
        if self.clearing_tags:
            asked = UpdateDeploymentInput(
                name=self.named,
                replica_count=self.replicas,
                open_to_public=self.opening,
                tags=None,
            )
        else:
            asked = UpdateDeploymentInput(
                name=self.named, replica_count=self.replicas, open_to_public=self.opening
            )
        with ActingAs(laid.caller):
            payload = await adapter.update(asked, wanted)
        return payload.deployment


@dataclass(frozen=True)
class TheNameChangesAndNothingElse(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-renames-a-deployment"

    @override
    def describe(self) -> str:
        return "수정 권한을 받은 사용자가 이름을 바꾸면, 이름만 새 값이 되고 나머지는 그대로다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class TheReplicaCountChanges(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-raises-the-replica-count"

    @override
    def describe(self) -> str:
        return "수정 권한을 받은 사용자가 복제 수를 올리면, 두려는 복제 수가 새 값이 된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), replica_count=1)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(replicas=3)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, replicas=3)


@dataclass(frozen=True)
class TheTagsAreCleared(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-the-tags-of-a-deployment-leaves-none"

    @override
    def describe(self) -> str:
        return "태그가 붙은 배포의 태그를 비우면, 태그가 하나도 남지 않는다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), tag=KEPT)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(clearing_tags=True)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started)


@dataclass(frozen=True)
class ItIsOpenedToThePublic(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-opens-a-deployment-to-the-public"

    @override
    def describe(self) -> str:
        return "공개가 아닌 배포를 수정 권한을 받은 사용자가 공개로 바꾸면, 공개로 바뀐 상태가 온다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), open_to_public=False)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(opening=True)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, open_to_public=True)


@dataclass(frozen=True)
class TheSuperadminEditsAnothers(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renames-anothers-deployment-without-a-grant"

    @override
    def describe(self) -> str:
        return (
            "다른 사람이 만든 배포의 이름을 아무 권한도 받지 않은 슈퍼관리자가 바꾸면, "
            "이름만 새 값이 된다. 역할이 권한 그래프를 지나간다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return AnothersDeploymentAndASuperadmin()

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ReadingIsNotEnoughToEdit(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-update-a-deployment"

    @override
    def describe(self) -> str:
        return "읽기 권한만 받은 사용자가 배포를 수정하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EditingAnUnknownIdIsNotFoundForASuperadmin(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아무것도 갖지 않은 id를 수정하면, 대상이 없다는 것으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED, other=uuid4())

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(EndpointNotFound)


SCENARIOS: list[EditingStep] = [
    TheNameChangesAndNothingElse(started=datetime.now(UTC)),
    TheReplicaCountChanges(started=datetime.now(UTC)),
    TheTagsAreCleared(started=datetime.now(UTC)),
    ItIsOpenedToThePublic(started=datetime.now(UTC)),
    TheSuperadminEditsAnothers(started=datetime.now(UTC)),
    ReadingIsNotEnoughToEdit(),
    EditingAnUnknownIdIsNotFoundForASuperadmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
