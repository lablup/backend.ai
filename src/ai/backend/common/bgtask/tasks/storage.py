from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import VFolderID

from .base import BaseBackgroundTaskFunction, BaseBackgroundTaskFunctionArgs


@dataclass
class CloneVFolderArgs(BaseBackgroundTaskFunctionArgs):
    """Arguments for cloning a virtual folder"""

    src_vfolder_id: VFolderID
    dst_vfolder_id: VFolderID

    @override
    def to_metadata_body(self) -> dict[str, Any]:
        return {
            "src_vfolder_id": str(self.src_vfolder_id),
            "dst_vfolder_id": str(self.dst_vfolder_id),
        }

    @classmethod
    @override
    def from_metadata_body(cls, body: dict[str, Any]) -> "CloneVFolderArgs":
        return cls(
            src_vfolder_id=VFolderID.from_str(body["src_vfolder_id"]),
            dst_vfolder_id=VFolderID.from_str(body["dst_vfolder_id"]),
        )


class CloneVFolder(BaseBackgroundTaskFunction[CloneVFolderArgs]):
    """Arguments for cloning a virtual folder"""

    source_vfolder_id: str

    @override
    async def execute(self, args: CloneVFolderArgs) -> None:
        pass

    @classmethod
    @override
    def get_name(cls) -> str:
        return "clone_vfolder"
