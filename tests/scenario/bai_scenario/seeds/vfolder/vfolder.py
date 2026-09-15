"""Write specs for a folder.

A folder lands in a project: a person's own in the project that is theirs alone, a
project's in that project. Which one is the creator's to settle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderOperationStatus
from ai.backend.manager.models.vfolder.creators import (
    PersonalVFolderCreator,
    ProjectVFolderCreator,
)
from bai_scenario.seeds.seeder import Naming, SeedRowFrom, SeedRowFromTwo


@dataclass(frozen=True)
class SeedPersonalVFolder(SeedRowFrom[UserData, VFolderData]):
    """A ready folder of the given person's own, on the given host."""

    host: str
    name_hint: str = "folder"

    @override
    def kind(self) -> str:
        return "개인 폴더"

    @override
    def detail(self) -> str:
        return "그 사람의 개인 프로젝트에 놓이고, 쓸 수 있는 상태다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: UserData) -> PersonalVFolderCreator:
        return PersonalVFolderCreator(
            name=name,
            domain_name=source.domain_name,
            quota_scope_id=str(QuotaScopeID(QuotaScopeType.USER, source.id)),
            host=self.host,
            creator_id=source.id,
            status=VFolderOperationStatus.READY,
            user=UserID(source.id),
        )


@dataclass(frozen=True)
class SeedProjectVFolder(SeedRowFromTwo[ProjectData, UserData, VFolderData]):
    """A ready folder of the given project, made by the given person, on the given host."""

    host: str
    name_hint: str = "folder"

    @override
    def kind(self) -> str:
        return "프로젝트 폴더"

    @override
    def detail(self) -> str:
        return "프로젝트에 놓이고, 쓸 수 있는 상태다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, first: ProjectData, second: UserData) -> ProjectVFolderCreator:
        return ProjectVFolderCreator(
            name=name,
            domain_name=first.domain_name,
            quota_scope_id=str(QuotaScopeID(QuotaScopeType.PROJECT, first.id)),
            host=self.host,
            creator_id=second.id,
            status=VFolderOperationStatus.READY,
            project=ProjectID(first.id),
        )
