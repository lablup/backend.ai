from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
)
from ai.backend.common.events.event_types.vfolder.anycast import VFolderDeleteRequestEvent

from .handlers import VFolderEventHandler


class Dispatchers:
    _vfolder_event_handler: VFolderEventHandler

    def __init__(self, bgtask_manager: BackgroundTaskManager) -> None:
        self._vfolder_event_handler = VFolderEventHandler(bgtask_manager)

    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        self._dispatch_vfolder_events(event_dispatcher)

    def _dispatch_vfolder_events(self, event_dispatcher: EventDispatcher) -> None:
        event_dispatcher.consume(
            VFolderDeleteRequestEvent,
            None,
            self._vfolder_event_handler.handle_vfolder_delete,
        )
