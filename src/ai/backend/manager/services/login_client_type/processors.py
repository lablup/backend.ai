from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
    CreateLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
    DeleteLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
    GetLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    SearchLoginClientTypesAction,
    SearchLoginClientTypesActionResult,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
    UpdateLoginClientTypeActionResult,
)
from ai.backend.manager.services.login_client_type.admin_service import (
    LoginClientTypeAdminService,
)
from ai.backend.manager.services.login_client_type.service import LoginClientTypeService


class LoginClientTypeProcessors(AbstractProcessorPackage):
    get: ActionProcessor[GetLoginClientTypeAction, GetLoginClientTypeActionResult]
    search: ActionProcessor[SearchLoginClientTypesAction, SearchLoginClientTypesActionResult]

    def __init__(
        self,
        service: LoginClientTypeService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.get = ActionProcessor(service.get, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            GetLoginClientTypeAction.spec(),
            SearchLoginClientTypesAction.spec(),
        ]


class LoginClientTypeAdminProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateLoginClientTypeAction, CreateLoginClientTypeActionResult]
    update: ActionProcessor[UpdateLoginClientTypeAction, UpdateLoginClientTypeActionResult]
    delete: ActionProcessor[DeleteLoginClientTypeAction, DeleteLoginClientTypeActionResult]

    def __init__(
        self,
        service: LoginClientTypeAdminService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateLoginClientTypeAction.spec(),
            UpdateLoginClientTypeAction.spec(),
            DeleteLoginClientTypeAction.spec(),
        ]
