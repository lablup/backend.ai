"""Write specs for a folder.

A folder lands in a project: a person's own in the project that is theirs alone, a
project's in that project. Which one is the creator's to settle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderOperationStatus
from ai.backend.manager.models.vfolder.creators import (
    PersonalVFolderCreator,
    ProjectVFolderCreator,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFrom, TestSeedRowFromTwo, joined


@dataclass(frozen=True)
class TestSeedPersonalVFolder(TestSeedRowFrom[UserData, VFolderData]):
    """A ready folder of the given person's own, on the given host."""

    host: str
    name_hint: str = "folder"
    default_mount_permission: VFolderMountPolicy | None = None

    @override
    def kind(self) -> str:
        return Says("개인 vfolder", english="Personal vfolder")

    @override
    def detail(self) -> str:
        parts: list[str] = [
            Says(
                "그 사람의 개인 프로젝트에 놓이고, 사용할 수 있는 상태입니다",
                english="is placed in that person's personal project and is ready to use",
            )
        ]
        if self.default_mount_permission is not None:
            permission = self.default_mount_permission.value
            parts.append(
                Says(
                    f"남에게는 {permission}로 마운트됩니다",
                    english=f"is mounted for others as {permission}",
                )
            )
        return joined(parts)

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
            default_mount_permission=self.default_mount_permission,
        )


@dataclass(frozen=True)
class TestSeedProjectVFolder(TestSeedRowFromTwo[ProjectData, UserData, VFolderData]):
    """A ready folder of the given project, made by the given person, on the given host."""

    host: str
    name_hint: str = "folder"
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL

    @override
    def kind(self) -> str:
        return Says("프로젝트 vfolder", english="Project vfolder")

    @override
    def detail(self) -> str:
        if self.usage_mode is VFolderUsageMode.GENERAL:
            return Says(
                "프로젝트에 놓이고, 사용할 수 있는 상태입니다",
                english="is placed in the project and is ready to use",
            )
        return Says(
            f"프로젝트에 놓이고, 사용할 수 있는 상태이며, 용도는 {self.usage_mode.value}입니다",
            english=(
                f"is placed in the project, is ready to use, and is for {self.usage_mode.value}"
            ),
        )

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
            usage_mode=self.usage_mode,
        )
