from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions.create_cluster_template import (
    CreateClusterTemplateAction,
    CreateClusterTemplateActionResult,
)
from .actions.create_task_template import (
    CreateTaskTemplateAction,
    CreateTaskTemplateActionResult,
)
from .actions.delete_cluster_template import (
    DeleteClusterTemplateAction,
    DeleteClusterTemplateActionResult,
)
from .actions.delete_task_template import (
    DeleteTaskTemplateAction,
    DeleteTaskTemplateActionResult,
)
from .actions.get_cluster_template import (
    GetClusterTemplateAction,
    GetClusterTemplateActionResult,
)
from .actions.get_task_template import (
    GetTaskTemplateAction,
    GetTaskTemplateActionResult,
)
from .actions.list_cluster_templates import (
    ListClusterTemplatesAction,
    ListClusterTemplatesActionResult,
)
from .actions.list_task_templates import (
    ListTaskTemplatesAction,
    ListTaskTemplatesActionResult,
)
from .actions.update_cluster_template import (
    UpdateClusterTemplateAction,
    UpdateClusterTemplateActionResult,
)
from .actions.update_task_template import (
    UpdateTaskTemplateAction,
    UpdateTaskTemplateActionResult,
)
from .service import TemplateService

__all__ = ("TemplateProcessors",)


class TemplateProcessors(AbstractProcessorPackage):
    """Processor package for session and cluster template operations."""

    create_task: ActionProcessor[CreateTaskTemplateAction, CreateTaskTemplateActionResult]
    list_task: ActionProcessor[ListTaskTemplatesAction, ListTaskTemplatesActionResult]
    get_task: ActionProcessor[GetTaskTemplateAction, GetTaskTemplateActionResult]
    update_task: ActionProcessor[UpdateTaskTemplateAction, UpdateTaskTemplateActionResult]
    delete_task: ActionProcessor[DeleteTaskTemplateAction, DeleteTaskTemplateActionResult]

    create_cluster: ActionProcessor[CreateClusterTemplateAction, CreateClusterTemplateActionResult]
    list_cluster: ActionProcessor[ListClusterTemplatesAction, ListClusterTemplatesActionResult]
    get_cluster: ActionProcessor[GetClusterTemplateAction, GetClusterTemplateActionResult]
    update_cluster: ActionProcessor[UpdateClusterTemplateAction, UpdateClusterTemplateActionResult]
    delete_cluster: ActionProcessor[DeleteClusterTemplateAction, DeleteClusterTemplateActionResult]

    def __init__(self, service: TemplateService, action_monitors: list[ActionMonitor]) -> None:
        self.create_task = ActionProcessor(service.create_task_template, action_monitors)
        self.list_task = ActionProcessor(service.list_task_templates, action_monitors)
        self.get_task = ActionProcessor(service.get_task_template, action_monitors)
        self.update_task = ActionProcessor(service.update_task_template, action_monitors)
        self.delete_task = ActionProcessor(service.delete_task_template, action_monitors)

        self.create_cluster = ActionProcessor(service.create_cluster_template, action_monitors)
        self.list_cluster = ActionProcessor(service.list_cluster_templates, action_monitors)
        self.get_cluster = ActionProcessor(service.get_cluster_template, action_monitors)
        self.update_cluster = ActionProcessor(service.update_cluster_template, action_monitors)
        self.delete_cluster = ActionProcessor(service.delete_cluster_template, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateTaskTemplateAction.spec(),
            ListTaskTemplatesAction.spec(),
            GetTaskTemplateAction.spec(),
            UpdateTaskTemplateAction.spec(),
            DeleteTaskTemplateAction.spec(),
            CreateClusterTemplateAction.spec(),
            ListClusterTemplatesAction.spec(),
            GetClusterTemplateAction.spec(),
            UpdateClusterTemplateAction.spec(),
            DeleteClusterTemplateAction.spec(),
        ]
