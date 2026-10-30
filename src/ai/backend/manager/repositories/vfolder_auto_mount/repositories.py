from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)

__all__ = ("VFolderAutoMountRepositories",)


@dataclass
class VFolderAutoMountRepositories:
    repository: VFolderAutoMountRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        return cls(repository=VFolderAutoMountRepository(args.v2_ops_provider))
