from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, CreatedEntityOpsResult
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.get_all import (
    GetAllNamespacesAction,
    GetAllNamespacesActionResult,
)
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
    UnregisterNamespaceActionResult,
)
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService


class StorageNamespaceProcessors:
    """Registration and the reads run against ops; two operations keep their service."""

    register: GlobalActionProcessor[
        RegisterNamespaceAction, CreatedEntityOpsResult[StorageNamespaceData]
    ]
    search: GlobalActionProcessor[
        SearchStorageNamespacesAction, BatchOpsResult[StorageNamespaceData]
    ]
    get_namespaces: GlobalActionProcessor[GetNamespacesAction, BatchOpsResult[StorageNamespaceData]]
    unregister: GlobalActionProcessor[UnregisterNamespaceAction, UnregisterNamespaceActionResult]
    get_all_namespaces: GlobalActionProcessor[GetAllNamespacesAction, GetAllNamespacesActionResult]

    def __init__(
        self,
        service: StorageNamespaceService,
        group: ProcessorGroup[StorageNamespaceData],
    ) -> None:
        self.register = group.global_create_ops(RegisterNamespaceAction)
        self.search = group.global_search_ops(SearchStorageNamespacesAction)
        self.get_namespaces = group.global_search_ops(GetNamespacesAction)
        self.unregister = group.global_scope(UnregisterNamespaceAction, service.unregister)
        self.get_all_namespaces = group.global_scope(
            GetAllNamespacesAction, service.get_all_namespaces
        )
