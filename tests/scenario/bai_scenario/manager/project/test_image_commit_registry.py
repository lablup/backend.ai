"""프로젝트 설정과 별도로 image commit을 위한 Container Registry를 읽는다."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.data.container_registry.types import ImageCommitRegistry
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy

type Targets = Sequence[ImageCommitRegistry | Exception | None]


@dataclass(frozen=True)
class ProjectAndTarget:
    project: ProjectData
    target: ImageCommitRegistry
    caller: UserData


@dataclass(frozen=True)
class ProjectWithReadPermission(Given[SeedingSession, ProjectAndTarget]):
    configured: bool
    may_read: bool

    @override
    def describe(self) -> str:
        return f"image commit을 위한 Container Registry 설정은 {self.configured}, 일반 사용자의 읽기 권한은 {self.may_read}"

    @override
    async def lay(self, seeding: SeedingSession) -> ProjectAndTarget:
        domain = await seeding.creating(SeedDomain())
        policy = await seeding.once(SeedProjectPolicy())
        target = ImageCommitRegistry("registry.example.com", "images")
        project = await seeding.creating_from_two(
            SeedProject(container_registry=target if self.configured else None), domain, policy
        )
        caller = await seeding.within(SomeoneOf(domain))
        if self.may_read:
            role = await seeding.creating_from(SeedRole(lambda one: ProjectID(one.id)), project)
            await seeding.adding(SeedPermission(ProjectEntityType(), Permission.READ), role)
            await seeding.granting(
                role, caller, role_id=lambda one: one.id, user_id=lambda one: UserID(one.id)
            )
        return ProjectAndTarget(seeding.made(project), target, seeding.made(caller))


@dataclass(frozen=True)
class ReadingTargets(When[ProjectAndTarget, ProjectAdapter, Targets]):
    configured: bool

    @override
    def operation(self) -> str:
        return "batch_load_image_commit_registries"

    @override
    def describe(self, laid: ProjectAndTarget) -> str:
        return "같은 프로젝트의 image commit을 위한 Container Registry를 두 번 요청한다"

    @override
    async def call(self, adapter: ProjectAdapter, laid: ProjectAndTarget) -> Targets:
        id = ProjectID(laid.project.id)
        with ActingAs(laid.caller):
            return await adapter.batch_load_image_commit_registries([id, id])


@dataclass(frozen=True)
class TargetsInRequestOrder(Then[ProjectAndTarget, Targets]):
    configured: bool
    may_read: bool

    @override
    def says(self) -> str:
        return "요청마다 image commit을 위한 Container Registry나 빈 값 또는 권한 거부를 응답한다"

    @override
    def look(self, laid: ProjectAndTarget, answered: Answered[Targets]) -> list[Verdict]:
        values = answered.response
        assert values is not None, answered.raised
        if not self.may_read:
            return [
                Same("count", len(values), 2),
                *[
                    Refused(NotEnoughPermission, value if isinstance(value, Exception) else None)
                    for value in values
                ],
            ]
        target = laid.target if self.configured else None
        return [Same("targets", values, [target, target])]


@dataclass(frozen=True)
class ReadTargetsScenario(Scenario[SeedingSession, ProjectAndTarget, ProjectAdapter, Targets]):
    name: str
    description: str
    configured: bool = False
    may_read: bool = True

    @override
    def summary(self) -> str:
        return self.name

    @override
    def describe(self) -> str:
        return self.description

    @override
    def given(self) -> Given[SeedingSession, ProjectAndTarget]:
        return ProjectWithReadPermission(self.configured, self.may_read)

    @override
    def when(self) -> When[ProjectAndTarget, ProjectAdapter, Targets]:
        return ReadingTargets(self.configured)

    @override
    def then(self) -> Then[ProjectAndTarget, Targets]:
        return TargetsInRequestOrder(self.configured, self.may_read)


SCENARIOS = [
    ReadTargetsScenario(
        "read-targets-in-request-order",
        "읽기 권한이 있으면 요청 순서대로 image commit을 위한 Container Registry를 응답한다",
        configured=True,
    ),
    ReadTargetsScenario(
        "read-unconfigured-targets",
        "읽기 권한이 있고 image commit을 위한 Container Registry가 설정되지 않았으면 빈 값을 응답한다",
    ),
    ReadTargetsScenario(
        "target-read-requires-permission",
        "읽기 권한이 없으면 image commit을 위한 Container Registry 조회를 거부한다",
        may_read=False,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_targets(
    scenario: ReadTargetsScenario, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
