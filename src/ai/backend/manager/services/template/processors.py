from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

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

    def __init__(
        self,
        service: TemplateService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Scope-based actions (create, list) with RBAC validation
        self.create_task = ScopeActionProcessor(
            service.create_task_template, action_monitors, validators=[validators.rbac.scope]
        )
        self.list_task = ScopeActionProcessor(
            service.list_task_templates, action_monitors, validators=[validators.rbac.scope]
        )
        self.create_cluster = ScopeActionProcessor(
            service.create_cluster_template, action_monitors, validators=[validators.rbac.scope]
        )
        self.list_cluster = ScopeActionProcessor(
            service.list_cluster_templates, action_monitors, validators=[validators.rbac.scope]
        )

        # Single-entity actions (get, update, delete) with RBAC validation
        self.get_task = SingleEntityActionProcessor(
            service.get_task_template, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.update_task = SingleEntityActionProcessor(
            service.update_task_template,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_task = SingleEntityActionProcessor(
            service.delete_task_template,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.get_cluster = SingleEntityActionProcessor(
            service.get_cluster_template,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.update_cluster = SingleEntityActionProcessor(
            service.update_cluster_template,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.delete_cluster = SingleEntityActionProcessor(
            service.delete_cluster_template,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )

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
