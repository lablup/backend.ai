from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.storage_namespace.actions.get_all_namespaces import (
    GetAllNamespacesAction,
    GetAllNamespacesActionResult,
)
from ai.backend.manager.services.storage_namespace.actions.get_namespaces import (
    GetNamespacesAction,
    GetNamespacesActionResult,
)
from ai.backend.manager.services.storage_namespace.actions.register_namespace import (
    RegisterNamespaceAction,
    RegisterNamespaceActionResult,
)
from ai.backend.manager.services.storage_namespace.actions.unregister_namespace import (
    UnregisterNamespaceAction,
    UnregisterNamespaceActionResult,
)
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService


class StorageNamespaceProcessors(AbstractProcessorPackage):
    register_namespace: ActionProcessor[RegisterNamespaceAction, RegisterNamespaceActionResult]
    unregister_namespace: ActionProcessor[
        UnregisterNamespaceAction, UnregisterNamespaceActionResult
    ]
    get_namespaces: ActionProcessor[GetNamespacesAction, GetNamespacesActionResult]
    get_all_namespaces: ActionProcessor[GetAllNamespacesAction, GetAllNamespacesActionResult]

    def __init__(
        self, service: StorageNamespaceService, action_monitors: list[ActionMonitor]
    ) -> None:
        self.register_namespace = ActionProcessor(service.register_namespace, action_monitors)
        self.unregister_namespace = ActionProcessor(service.unregister_namespace, action_monitors)
        self.get_namespaces = ActionProcessor(service.get_namespaces, action_monitors)
        self.get_all_namespaces = ActionProcessor(service.get_all_namespaces, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            RegisterNamespaceAction.spec(),
            UnregisterNamespaceAction.spec(),
            GetNamespacesAction.spec(),
            GetAllNamespacesAction.spec(),
        ]
