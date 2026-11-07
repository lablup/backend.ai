"""Write specs for a project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromTwo


@dataclass(frozen=True)
class TestSeedProject(TestSeedRowFromTwo[DomainData, ProjectResourcePolicyData, ProjectData]):
    """A project of the given domain, under the given policy."""

    name_hint: str = "project"
    is_active: bool = True

    @override
    def kind(self) -> str:
        return Says("프로젝트", english="Project")

    @override
    def detail(self) -> str:
        if self.is_active:
            return Says("")
        return Says("비활성 상태", english="inactive")

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self, name: str, first: DomainData, second: ProjectResourcePolicyData
    ) -> ProjectCreator:
        return ProjectCreator(
            name=name,
            domain_id=first.id,
            domain_name=first.name,
            description=f"{name} was already here",
            resource_policy=second.name,
            is_active=self.is_active,
        )
