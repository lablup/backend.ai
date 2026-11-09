"""배포 고치기 — 무엇이 바뀌고, 누가 바꿀 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import UpdateDeploymentInput
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import (
    ADeploymentAndACaller,
    ADeploymentInThatPlace,
    AnothersDeploymentAndASuperadmin,
    TheDeploymentNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

RENAMED = "renamed"
KEPT = "keep"

type EditingStep = Scenario[
    TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode
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
        changed: list[Says] = []
        if self.named is not None:
            changed.append(Says(f"이름을 {self.named}으로", english=f"name to {self.named}"))
        if self.replicas is not None:
            changed.append(
                Says(f"복제 수를 {self.replicas}으로", english=f"replica count to {self.replicas}")
            )
        if self.clearing_tags:
            changed.append(Says("태그를 비우도록", english="clearing the tags"))
        if self.opening is not None:
            changed.append(
                Says("바깥에 열도록", english="opening it to the public")
                if self.opening
                else Says("바깥에 닫도록", english="closing it to the public")
            )
        called = (
            Says("아무것도 갖지 않은 id", english="an id nothing answers to")
            if self.other is not None
            else laid.deployment.metadata.name
        )
        korean = ", ".join(in_language(one, Language.KOREAN) for one in changed)
        english = ", ".join(in_language(one, Language.ENGLISH) for one in changed)
        english_change = f" with {english}" if english else " without giving a value"
        return Says(
            f"{laid.caller.username} 이 {called}를 {korean or '아무것도 지정하지 않고'} 수정합니다",
            english=(
                f"{laid.caller.username} updates {in_language(called, Language.ENGLISH)}"
                f"{english_change}"
            ),
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
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-renames-a-deployment"

    @override
    def describe(self) -> str:
        return Says(
            "수정 권한을 받은 사용자가 이름을 변경하면, 이름만 새 값이 되고 나머지는 그대로입니다",
            english=(
                "when a user granted update changes the name, only the name becomes the new value "
                "and everything else stays the same"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class TheReplicaCountChanges(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-raises-the-replica-count"

    @override
    def describe(self) -> str:
        return Says(
            "수정 권한을 받은 사용자가 복제 수를 올리면, 두려는 복제 수가 새 값이 됩니다",
            english=(
                "when a user granted update raises the replica count, the intended replica count "
                "becomes the new value"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), replica_count=1)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(replicas=3)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, replicas=3)


@dataclass(frozen=True)
class TheTagsAreCleared(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "clearing-the-tags-of-a-deployment-leaves-none"

    @override
    def describe(self) -> str:
        return Says(
            "태그가 붙은 배포의 태그를 비우면, 태그가 하나도 남지 않습니다",
            english="clearing the tags of a deployment that holds tags leaves no tag",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), tag=KEPT)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(clearing_tags=True)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started)


@dataclass(frozen=True)
class ItIsOpenedToThePublic(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-opens-a-deployment-to-the-public"

    @override
    def describe(self) -> str:
        return Says(
            "공개가 아닌 배포를 수정 권한을 받은 사용자가 공개로 변경하면, 공개로 변경된 상태가 옵니다",
            english=(
                "when a user granted update changes a deployment that is not public to public, "
                "the state comes back changed to public"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.UPDATE,), open_to_public=False)

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(opening=True)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, open_to_public=True)


@dataclass(frozen=True)
class TheSuperadminEditsAnothers(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-renames-anothers-deployment-without-a-grant"

    @override
    def describe(self) -> str:
        return Says(
            "다른 사람이 생성한 배포의 이름을 아무 권한도 받지 않은 superadmin 이 변경하면, "
            "이름만 새 값이 됩니다. 역할이 권한 그래프를 지나갑니다",
            english=(
                "when a superadmin holding no grant changes the name of a deployment another user "
                "created, only the name becomes the new value; the role passes through the "
                "permission graph"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return AnothersDeploymentAndASuperadmin()

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheDeploymentNode(started=self.started, named=RENAMED)


@dataclass(frozen=True)
class ReadingIsNotEnoughToEdit(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-update-a-deployment"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 배포를 수정하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read updates a deployment, the call is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]:
        return Editing(named=RENAMED)

    @override
    def then(self) -> Then[ADeploymentAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EditingAnUnknownIdIsNotFoundForASuperadmin(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아무것도 갖지 않은 id 를 수정하면, 대상이 없다는 것으로 거부됩니다",
            english=(
                "when a superadmin updates an id nothing answers to, the call is rejected as not "
                "found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
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
