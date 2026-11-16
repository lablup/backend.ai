"""프로젝트가 허용된 Container Registry를 default 여부와 함께 읽는다."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    ProjectAllowedRegistryData,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.image.registry import (
    AllowProject,
    AllowProjectAsDefault,
    TestSeedContainerRegistry,
)
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy

type Registries = Sequence[list[ProjectAllowedRegistryData] | Exception | None]
type Link = Literal["default", "allowed"] | None


@dataclass(frozen=True)
class ProjectAndRegistry:
    project: ProjectData
    registry: ContainerRegistryData
    caller: UserData


@dataclass(frozen=True)
class ProjectWithReadPermission(Given[TestSeedingSession, ProjectAndRegistry]):
    link: Link
    may_read: bool

    @override
    def describe(self) -> str:
        if self.link == "default":
            registry_ko = "프로젝트가 레지스트리에 default 로 허용돼 있습니다"
            registry_en = "the project is allowed on the registry as the default"
        elif self.link == "allowed":
            registry_ko = "프로젝트가 레지스트리에 허용돼 있지만 default 는 아닙니다"
            registry_en = "the project is allowed on the registry but not as the default"
        else:
            registry_ko = "프로젝트에 허용된 레지스트리가 없습니다"
            registry_en = "the project has no allowed registry"
        if self.may_read:
            permission_ko, permission_en = "있습니다", "has"
        else:
            permission_ko, permission_en = "없습니다", "has no"
        return Says(
            f"{registry_ko}. 일반 사용자는 프로젝트 읽기 권한이 {permission_ko}.",
            english=(
                f"{registry_en}. A regular user {permission_en} read permission on the project."
            ),
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> ProjectAndRegistry:
        domain = await seeding.creating(TestSeedDomain())
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(), domain, policy)
        registry = await seeding.creating(TestSeedContainerRegistry(project="images"))
        match self.link:
            case "default":
                await seeding.linking(AllowProjectAsDefault(), project, registry)
            case "allowed":
                await seeding.linking(AllowProject(), project, registry)
            case None:
                pass
        caller = await seeding.within(SomeoneOf(domain))
        if self.may_read:
            role = await seeding.creating_from(TestSeedRole(lambda one: ProjectID(one.id)), project)
            await seeding.adding(TestSeedPermission(ProjectEntityType(), Permission.READ), role)
            await seeding.granting(
                role, caller, role_id=lambda one: one.id, user_id=lambda one: UserID(one.id)
            )
        return ProjectAndRegistry(
            seeding.made(project), seeding.made(registry), seeding.made(caller)
        )


@dataclass(frozen=True)
class ReadingRegistries(When[ProjectAndRegistry, ProjectAdapter, Registries]):
    @override
    def operation(self) -> str:
        return "batch_load_registries"

    @override
    def describe(self, laid: ProjectAndRegistry) -> str:
        return Says(
            "같은 프로젝트의 허용된 Container Registry 를 두 번 요청합니다",
            english="asks for the allowed container registries of the same project twice",
        )

    @override
    async def call(self, adapter: ProjectAdapter, laid: ProjectAndRegistry) -> Registries:
        id = ProjectID(laid.project.id)
        with ActingAs(laid.caller):
            return await adapter.batch_load_registries([id, id])


@dataclass(frozen=True)
class RegistriesInRequestOrder(Then[ProjectAndRegistry, Registries]):
    link: Link
    may_read: bool

    @override
    def says(self) -> str:
        return Says(
            "요청마다 허용된 Container Registry 목록이나 권한 거부를 응답합니다",
            english=(
                "answers each request with the allowed container registries or a "
                "permission rejection"
            ),
        )

    @override
    def look(self, laid: ProjectAndRegistry, answered: Answered[Registries]) -> list[Verdict]:
        values = answered.response
        assert values is not None, answered.raised
        verdicts: list[Verdict] = [Same("count", len(values), 2)]
        if not self.may_read:
            for value in values:
                verdicts.append(
                    Refused(NotEnoughPermission, value if isinstance(value, Exception) else None)
                )
            return verdicts
        for i, value in enumerate(values):
            assert isinstance(value, list), value
            verdicts.append(Same(f"[{i}] count", len(value), 0 if self.link is None else 1))
            for j, entry in enumerate(value):
                verdicts.append(
                    Held(
                        f"[{i}][{j}].registry",
                        entry.registry,
                        SameAs(
                            laid.registry,
                            Says(
                                "미리 저장한 레지스트리", english="the registry seeded in advance"
                            ),
                        ),
                    )
                )
                verdicts.append(
                    Same(f"[{i}][{j}].is_default", entry.is_default, self.link == "default")
                )
        return verdicts


@dataclass(frozen=True)
class ReadRegistriesScenario(
    Scenario[TestSeedingSession, ProjectAndRegistry, ProjectAdapter, Registries]
):
    name: str
    description: Says
    link: Link = None
    may_read: bool = True

    @override
    def summary(self) -> str:
        return self.name

    @override
    def describe(self) -> str:
        return self.description

    @override
    def given(self) -> Given[TestSeedingSession, ProjectAndRegistry]:
        return ProjectWithReadPermission(self.link, self.may_read)

    @override
    def when(self) -> When[ProjectAndRegistry, ProjectAdapter, Registries]:
        return ReadingRegistries()

    @override
    def then(self) -> Then[ProjectAndRegistry, Registries]:
        return RegistriesInRequestOrder(self.link, self.may_read)


SCENARIOS = [
    ReadRegistriesScenario(
        "read-default-registry",
        Says(
            "읽기 권한이 있으면 default 로 허용된 Container Registry 를 default 라는 표시와 "
            "함께 응답합니다",
            english=(
                "with read permission, answers the container registry allowed as the "
                "default with a flag saying it is the default"
            ),
        ),
        link="default",
    ),
    ReadRegistriesScenario(
        "read-allowed-registry",
        Says(
            "읽기 권한이 있으면 default 가 아닌 허용된 Container Registry 도 default 가 "
            "아니라는 표시와 함께 응답합니다",
            english=(
                "with read permission, answers a container registry allowed but not as "
                "the default with a flag saying it is not the default"
            ),
        ),
        link="allowed",
    ),
    ReadRegistriesScenario(
        "read-no-registry",
        Says(
            "읽기 권한이 있고 허용된 Container Registry 가 없으면 빈 목록을 응답합니다",
            english=(
                "with read permission and no allowed container registry, answers an empty list"
            ),
        ),
    ),
    ReadRegistriesScenario(
        "registries-read-requires-permission",
        Says(
            "읽기 권한이 없으면 허용된 Container Registry 조회를 거부합니다",
            english=("without read permission, rejects the read of allowed container registries"),
        ),
        may_read=False,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_registries(
    scenario: ReadRegistriesScenario, adapter: ProjectAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
