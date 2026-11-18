"""Write spec for a vfolder auto-mount."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderMountPermission
from ai.backend.manager.data.vfolder_auto_mount.types import (
    VFolderAutoMountData,
    VFolderAutoMountSpec,
)
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromTwo, joined


@dataclass(frozen=True)
class TestSeedVFolderAutoMount(TestSeedRowFromTwo[VFolderData, UserData, VFolderAutoMountData]):
    """A folder mounted into every session created in the folder's own scope.

    ``in_project`` must agree with the folder: a project folder is mounted for the
    project, a personal folder for the user who owns it.
    """

    in_project: bool = True
    mount_destination: str = "/home/work/extra"
    subpath: str = "."
    mount_permission: VFolderMountPermission = VFolderMountPermission.READ_ONLY

    @override
    def kind(self) -> str:
        return Says("vfolder 자동 마운트", english="Vfolder auto-mount")

    @override
    def detail(self) -> str:
        parts = [
            Says(
                f"{self.mount_destination} 에 {self.mount_permission.value} 로 마운트됩니다",
                english=(
                    f"is mounted at {self.mount_destination} with {self.mount_permission.value}"
                ),
            )
        ]
        if self.subpath != ".":
            parts.append(
                Says(
                    f"폴더 안 {self.subpath} 만 마운트됩니다",
                    english=f"only {self.subpath} inside the folder is mounted",
                )
            )
        return joined(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming("auto-mount")

    @override
    def seed(self, name: str, first: VFolderData, second: UserData) -> VFolderAutoMountCreator:
        return VFolderAutoMountCreator(
            scope=self._scope(first),
            spec=VFolderAutoMountSpec(
                vfolder_id=VFolderUUID(first.id),
                mount_destination=self.mount_destination,
                subpath=self.subpath,
                mount_permission=self.mount_permission,
            ),
        )

    def _scope(self, folder: VFolderData) -> EntityIdentifier:
        if self.in_project:
            if folder.group is None:
                raise LookupError("the folder is not placed in a project")
            return ProjectID(folder.group)
        if folder.user is None:
            raise LookupError("the folder is not owned by a user")
        return UserID(folder.user)
