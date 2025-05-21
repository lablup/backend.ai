import logging

from ai.backend.common.events.vfolder import (
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter

from ..models.utils import (
    ExtendedAsyncSAEngine,
)
from ..models.vfolder import VFolderOperationStatus, update_vfolder_status

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderEventHandler:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def handle_vfolder_deletion_success(
        self,
        context: None,
        source: AgentId,
        event: VFolderDeletionSuccessEvent,
    ) -> None:
        await update_vfolder_status(
            self._db, [event.vfid.folder_id], VFolderOperationStatus.DELETE_COMPLETE, do_log=True
        )

    async def handle_vfolder_deletion_failure(
        self,
        context: None,
        source: AgentId,
        event: VFolderDeletionFailureEvent,
    ) -> None:
        log.exception(f"Failed to delete vfolder (vfid:{event.vfid}, msg:{event.message})")
        await update_vfolder_status(
            self._db, [event.vfid.folder_id], VFolderOperationStatus.DELETE_ERROR, do_log=True
        )
