"""Write specs for a project."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRowFromTwo

from ai.backend.common.types import VFolderHostPermission, VFolderHostPermissionMap
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.project.creators import ProjectCreator


@dataclass(frozen=True)
class SeedProject(SeedRowFromTwo[DomainData, ProjectResourcePolicyData, ProjectData]):
    """A project of the given domain, under the given policy.

    ``vfolder_hosts`` are the storage hosts a folder this project owns may land on. The
    project row carries them itself rather than reading them off the policy, so a folder
    made under a project with none is refused by the host before anything is written.
    """

    name_hint: str = "project"
    vfolder_hosts: Sequence[str] = field(default_factory=tuple)

    @override
    def kind(self) -> str:
        return "프로젝트"

    @override
    def detail(self) -> str:
        if not self.vfolder_hosts:
            return ""
        return f"이 프로젝트의 폴더는 {', '.join(self.vfolder_hosts)}에 놓을 수 있다"

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
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                host: set(VFolderHostPermission) for host in self.vfolder_hosts
            }),
        )
