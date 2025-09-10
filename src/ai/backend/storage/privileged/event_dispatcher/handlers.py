from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.events.event_types.vfolder.anycast import VFolderDeleteRequestEvent
from ai.backend.common.types import AgentId

from ...bgtask.tags import PRIVILEGED_WORKER_TAG
from ...bgtask.tasks.delete import VFolderDeleteTaskArgs


class VFolderEventHandler:
    def __init__(
        self,
        bgtask_manager: BackgroundTaskManager,
    ) -> None:
        self._bgtask_manager = bgtask_manager

    async def handle_vfolder_delete(
        self,
        context: None,
        source: AgentId,
        event: VFolderDeleteRequestEvent,
    ) -> None:
        delete_args = VFolderDeleteTaskArgs(
            volume=event.volume,
            vfolder_id=event.vfid,
        )
        await self._bgtask_manager.start_retriable(
            TaskName.DELETE_VFOLDER,
            delete_args,
            tags=[PRIVILEGED_WORKER_TAG],
        )
