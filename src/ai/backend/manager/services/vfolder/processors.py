from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.vfolder.actions.get_task_logs import (
    GetTaskLogsAction,
    GetTaskLogsActionResult,
)
from ai.backend.manager.services.vfolder.service import VFolderService


class VFolderProcessors:
    get_task_logs: ActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]

    def __init__(self, service: VFolderService) -> None:
        self.get_task_logs = ActionProcessor(service.get_task_logs)
