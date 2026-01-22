from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.group_config.actions.create_dotfile import (
    CreateDotfileAction,
    CreateDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.delete_dotfile import (
    DeleteDotfileAction,
    DeleteDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.get_dotfile import (
    GetDotfileAction,
    GetDotfileActionResult,
)
from ai.backend.manager.services.group_config.actions.list_dotfiles import (
    ListDotfilesAction,
    ListDotfilesActionResult,
)
from ai.backend.manager.services.group_config.actions.update_dotfile import (
    UpdateDotfileAction,
    UpdateDotfileActionResult,
)
from ai.backend.manager.services.group_config.service import GroupConfigService


class GroupConfigProcessors(AbstractProcessorPackage):
    create_dotfile: ActionProcessor[CreateDotfileAction, CreateDotfileActionResult]
    list_dotfiles: ActionProcessor[ListDotfilesAction, ListDotfilesActionResult]
    get_dotfile: ActionProcessor[GetDotfileAction, GetDotfileActionResult]
    update_dotfile: ActionProcessor[UpdateDotfileAction, UpdateDotfileActionResult]
    delete_dotfile: ActionProcessor[DeleteDotfileAction, DeleteDotfileActionResult]

    def __init__(self, service: GroupConfigService, action_monitors: list[ActionMonitor]) -> None:
        self.create_dotfile = ActionProcessor(service.create_dotfile, action_monitors)
        self.list_dotfiles = ActionProcessor(service.list_dotfiles, action_monitors)
        self.get_dotfile = ActionProcessor(service.get_dotfile, action_monitors)
        self.update_dotfile = ActionProcessor(service.update_dotfile, action_monitors)
        self.delete_dotfile = ActionProcessor(service.delete_dotfile, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDotfileAction.spec(),
            ListDotfilesAction.spec(),
            GetDotfileAction.spec(),
            UpdateDotfileAction.spec(),
            DeleteDotfileAction.spec(),
        ]
