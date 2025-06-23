from dataclasses import dataclass
from pathlib import PurePosixPath

from ai.backend.common.types import (
    MountPermission,
    VFolderID,
    VFolderUsageMode,
)


@dataclass
class VFolderMountData:
    name: str
    vfid: VFolderID
    vfsubpath: PurePosixPath
    host_path: PurePosixPath
    kernel_path: PurePosixPath
    mount_perm: MountPermission
    usage_mode: VFolderUsageMode
