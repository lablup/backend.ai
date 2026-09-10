"""Write specs for a project."""

from __future__ import annotations

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.project.creators import ProjectCreator
from bai_scenario.seeds.seeder import SpecFromTwo


def seed_project(
    *, name_hint: str = "project"
) -> SpecFromTwo[DomainData, ProjectResourcePolicyData, ProjectData]:
    """A project of the given domain, under the given policy."""

    def build(name: str, domain: DomainData, policy: ProjectResourcePolicyData) -> ProjectCreator:
        return ProjectCreator(
            name=name,
            domain_id=domain.id,
            domain_name=domain.name,
            description=f"{name} was already here",
            resource_policy=policy.name,
        )

    return SpecFromTwo("a project", name_hint, build)
