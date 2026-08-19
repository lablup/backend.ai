from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor

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


class TemplateProcessors:
    """Processor package for session and cluster template operations."""

    create_task: ScopeActionProcessor[CreateTaskTemplateAction, CreateTaskTemplateActionResult]
    list_task: ScopeActionProcessor[ListTaskTemplatesAction, ListTaskTemplatesActionResult]
    get_task: SingleEntityActionProcessor[GetTaskTemplateAction, GetTaskTemplateActionResult]
    update_task: SingleEntityActionProcessor[
        UpdateTaskTemplateAction, UpdateTaskTemplateActionResult
    ]
    delete_task: SingleEntityActionProcessor[
        DeleteTaskTemplateAction, DeleteTaskTemplateActionResult
    ]

    create_cluster: ScopeActionProcessor[
        CreateClusterTemplateAction, CreateClusterTemplateActionResult
    ]
    list_cluster: ScopeActionProcessor[ListClusterTemplatesAction, ListClusterTemplatesActionResult]
    get_cluster: SingleEntityActionProcessor[
        GetClusterTemplateAction, GetClusterTemplateActionResult
    ]
    update_cluster: SingleEntityActionProcessor[
        UpdateClusterTemplateAction, UpdateClusterTemplateActionResult
    ]
    delete_cluster: SingleEntityActionProcessor[
        DeleteClusterTemplateAction, DeleteClusterTemplateActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: TemplateService) -> None:
        self.create_task = group.scope(CreateTaskTemplateAction, service.create_task_template)
        self.list_task = group.scope(ListTaskTemplatesAction, service.list_task_templates)
        self.get_task = group.single_entity(GetTaskTemplateAction, service.get_task_template)
        self.update_task = group.single_entity(
            UpdateTaskTemplateAction, service.update_task_template
        )
        self.delete_task = group.single_entity(
            DeleteTaskTemplateAction, service.delete_task_template
        )

        self.create_cluster = group.scope(
            CreateClusterTemplateAction, service.create_cluster_template
        )
        self.list_cluster = group.scope(ListClusterTemplatesAction, service.list_cluster_templates)
        self.get_cluster = group.single_entity(
            GetClusterTemplateAction, service.get_cluster_template
        )
        self.update_cluster = group.single_entity(
            UpdateClusterTemplateAction, service.update_cluster_template
        )
        self.delete_cluster = group.single_entity(
            DeleteClusterTemplateAction, service.delete_cluster_template
        )
