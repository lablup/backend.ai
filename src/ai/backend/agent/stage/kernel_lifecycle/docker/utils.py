import os
from collections.abc import Collection
from pathlib import Path
from typing import Iterable, Optional, Self

from ai.backend.common.docker import KernelFeatures
from ai.backend.common.types import KernelId


class ScratchUtil:
    @classmethod
    def scratch_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (scratch_root / str(kernel_id)).resolve()

    @classmethod
    def scratch_file(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / f"{kernel_id}.img").resolve()

    @classmethod
    def tmp_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (scratch_root / f"{kernel_id}_tmp").resolve()

    @classmethod
    def work_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / "work").resolve()

    @classmethod
    def config_dir(cls, scratch_root: Path, kernel_id: KernelId) -> Path:
        return (cls.scratch_dir(scratch_root, kernel_id) / "config").resolve()


class PathOwnerDeterminer:
    """
    Determines the final UID and GID for a path based on overrides and kernel features.
    """

    def __init__(self, kernel_uid: int, kernel_gid: int, do_uid_match: bool) -> None:
        self._do_uid_match = do_uid_match
        self._kernel_uid = kernel_uid
        self._kernel_gid = kernel_gid

    @classmethod
    def by_kernel_features(
        cls,
        kernel_uid: int,
        kernel_gid: int,
        kernel_features: Collection[str],
    ) -> Self:
        """
        Create a PathOwnerDeterminer based on kernel features.
        If UID_MATCH is enabled, it uses kernel_uid/gid.
        Otherwise, it uses the current file's UID/GID.
        """
        do_uid_match = KernelFeatures.UID_MATCH in kernel_features
        return cls(kernel_uid=kernel_uid, kernel_gid=kernel_gid, do_uid_match=do_uid_match)

    def determine(
        self, path: Path, *, uid_override: Optional[int], gid_override: Optional[int]
    ) -> tuple[int, int]:
        """
        Determine the final UID and GID for a path.
        If uid_override/gid_override are provided, they are used.
        If not, and if uid-match feature is enabled, it uses kernel_uid/gid.
        Otherwise, it uses the current file's UID/GID.
        """
        pstat = path.stat()
        final_uid = (
            uid_override
            if uid_override is not None
            else (self._kernel_uid if self._do_uid_match else pstat.st_uid)
        )
        final_gid = (
            gid_override
            if gid_override is not None
            else (self._kernel_gid if self._do_uid_match else pstat.st_gid)
        )
        return final_uid, final_gid


class ChownUtil:
    def __init__(self) -> None:
        self._do_chown = 0 == os.geteuid()

    def chown_path(self, path: Path, uid: int, gid: int) -> None:
        """
        Change ownership of a single path if running as root.
        """
        if self._do_chown:
            os.chown(path, uid, gid)

    def chown_paths(self, paths: Iterable[Path], uid: int, gid: int) -> None:
        """
        Change ownership of multiple paths if running as root.
        """
        if self._do_chown:
            for p in paths:
                self.chown_path(p, uid, gid)
