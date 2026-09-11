"""Write specs for a folder that is already there when the request arrives.

A scenario that reads, deletes or restores a folder needs one standing before the call,
and the adapter is what the call tests rather than what sets it up. These lay the row
through the manager's own insert spec, the way the create path does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRowFrom, SeedRowFromTwo

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
)
from ai.backend.manager.models.vfolder.creators import (
    PersonalVFolderCreator,
    ProjectVFolderCreator,
)


@dataclass(frozen=True)
class SeedFolderOf(SeedRowFrom[UserData, VFolderData]):
    """A folder the given user owns, standing ready on the given host.

    The create path leaves a new row unusable until the storage host answers; a folder
    that was already there is past that, so it is laid ready.
    """

    host: str
    name_hint: str = "folder"
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def kind(self) -> str:
        return "폴더"

    @override
    def detail(self) -> str:
        if self.status is VFolderOperationStatus.DELETE_PENDING:
            return "소유자가 지워 휴지통에 있다"
        return "소유자가 이미 만들어 둔 것이다"

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
            user=UserID(source.id),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            cloneable=False,
            status=self.status,
        )


@dataclass(frozen=True)
class SeedProjectFolderOf(SeedRowFromTwo[UserData, ProjectData, VFolderData]):
    """A folder the given project owns, made by the given user."""

    host: str
    name_hint: str = "project-folder"

    @override
    def kind(self) -> str:
        return "프로젝트 폴더"

    @override
    def detail(self) -> str:
        return "프로젝트가 소유하고, 개인 소유자는 없다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, first: UserData, second: ProjectData) -> ProjectVFolderCreator:
        return ProjectVFolderCreator(
            name=name,
            domain_name=first.domain_name,
            quota_scope_id=str(QuotaScopeID(QuotaScopeType.PROJECT, ProjectID(second.id))),
            host=self.host,
            creator_id=first.id,
            project=ProjectID(second.id),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )
