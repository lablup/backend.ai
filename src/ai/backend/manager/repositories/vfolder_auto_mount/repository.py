from __future__ import annotations

from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("VFolderAutoMountRepository",)


class VFolderAutoMountRepository:
    """The create, whose spec carries a precondition. Every other operation runs
    against ``OpsRepository``."""

    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(self, creator: VFolderAutoMountCreator) -> VFolderAutoMountData:
        """Insert one auto-mount; a vfolder outside the project refuses the write."""
        async with self._ops.write_ops() as w:
            return await w.create_entity(creator)
