import logging

from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderCloneFailureEvent,
    VFolderCloneSuccessEvent,
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
)
from ai.backend.manager.models.vfolder import VFolderOperationStatus, update_vfolder_status

log = StructuredLogger(logging.getLogger(__spec__.name))


class VFolderEventHandler:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def handle_vfolder_deletion_success(
        self,
        _context: None,
        _source: AgentId,
        event: VFolderDeletionSuccessEvent,
    ) -> None:
        await update_vfolder_status(
            self._db, [event.vfid.folder_id], VFolderOperationStatus.DELETE_COMPLETE, do_log=True
        )

    async def handle_vfolder_deletion_failure(
        self,
        _context: None,
        _source: AgentId,
        event: VFolderDeletionFailureEvent,
    ) -> None:
        log.warning(
            "vfolder deletion failed", vfolder_id=event.vfid.folder_id, reason=event.message
        )
        await update_vfolder_status(
            self._db, [event.vfid.folder_id], VFolderOperationStatus.DELETE_ERROR, do_log=True
        )

    async def handle_vfolder_clone_success(
        self,
        _context: None,
        _source: AgentId,
        event: VFolderCloneSuccessEvent,
    ) -> None:
        await update_vfolder_status(
            self._db,
            [event.vfid.folder_id, event.dst_vfid.folder_id],
            VFolderOperationStatus.READY,
            do_log=True,
        )

    async def handle_vfolder_clone_failure(
        self,
        _context: None,
        _source: AgentId,
        event: VFolderCloneFailureEvent,
    ) -> None:
        log.warning(
            "vfolder clone failed",
            vfolder_id=event.vfid.folder_id,
            dst_vfolder_id=event.dst_vfid.folder_id,
            reason=event.message,
        )
        await update_vfolder_status(
            self._db, [event.vfid.folder_id], VFolderOperationStatus.READY, do_log=True
        )
