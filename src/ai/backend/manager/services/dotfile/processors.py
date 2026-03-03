from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions.check_group_membership import (
    CheckGroupMembershipAction,
    CheckGroupMembershipActionResult,
)
from .actions.create import CreateDotfileAction, CreateDotfileActionResult
from .actions.delete import DeleteDotfileAction, DeleteDotfileActionResult
from .actions.get_bootstrap import GetBootstrapScriptAction, GetBootstrapScriptActionResult
from .actions.list_or_get import ListOrGetDotfilesAction, ListOrGetDotfilesActionResult
from .actions.resolve_group import ResolveGroupAction, ResolveGroupActionResult
from .actions.update import UpdateDotfileAction, UpdateDotfileActionResult
from .actions.update_bootstrap import UpdateBootstrapScriptAction, UpdateBootstrapScriptActionResult
from .service import DotfileService

__all__ = ("DotfileProcessors",)


class DotfileProcessors(AbstractProcessorPackage):
    """Processor package for dotfile operations."""

    create: ActionProcessor[CreateDotfileAction, CreateDotfileActionResult]
    list_or_get: ActionProcessor[ListOrGetDotfilesAction, ListOrGetDotfilesActionResult]
    update: ActionProcessor[UpdateDotfileAction, UpdateDotfileActionResult]
    delete: ActionProcessor[DeleteDotfileAction, DeleteDotfileActionResult]
    resolve_group: ActionProcessor[ResolveGroupAction, ResolveGroupActionResult]
    check_group_membership: ActionProcessor[
        CheckGroupMembershipAction, CheckGroupMembershipActionResult
    ]
    get_bootstrap: ActionProcessor[GetBootstrapScriptAction, GetBootstrapScriptActionResult]
    update_bootstrap: ActionProcessor[
        UpdateBootstrapScriptAction, UpdateBootstrapScriptActionResult
    ]

    def __init__(self, service: DotfileService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create_dotfile, action_monitors)
        self.list_or_get = ActionProcessor(service.list_or_get_dotfiles, action_monitors)
        self.update = ActionProcessor(service.update_dotfile, action_monitors)
        self.delete = ActionProcessor(service.delete_dotfile, action_monitors)
        self.resolve_group = ActionProcessor(service.resolve_group, action_monitors)
        self.check_group_membership = ActionProcessor(
            service.check_group_membership, action_monitors
        )
        self.get_bootstrap = ActionProcessor(service.get_bootstrap_script, action_monitors)
        self.update_bootstrap = ActionProcessor(service.update_bootstrap_script, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDotfileAction.spec(),
            ListOrGetDotfilesAction.spec(),
            UpdateDotfileAction.spec(),
            DeleteDotfileAction.spec(),
            ResolveGroupAction.spec(),
            CheckGroupMembershipAction.spec(),
            GetBootstrapScriptAction.spec(),
            UpdateBootstrapScriptAction.spec(),
        ]
