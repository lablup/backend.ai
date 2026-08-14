from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
from ai.backend.manager.services.storage_namespace.actions.resolve_by_namespace import (
    ResolveStorageNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.actions.search import (
    SearchStorageNamespacesAction,
)
from ai.backend.manager.services.storage_namespace.actions.unregister import (
    UnregisterNamespaceAction,
)


class StorageNamespaceProcessors:
    """Every operation runs against ops; the domain keeps no service of its own.

    Removal is keyed on the id like every other purge, and the (storage, namespace)
    pair the registration API exposes reaches it through the lookup.
    """

    register: GlobalActionProcessor[
        RegisterNamespaceAction, CreatedEntityOpsResult[StorageNamespaceData]
    ]
    search: GlobalActionProcessor[
        SearchStorageNamespacesAction, BatchOpsResult[StorageNamespaceData]
    ]
    get_namespaces: GlobalActionProcessor[GetNamespacesAction, BatchOpsResult[StorageNamespaceData]]
    lookup: LookupActionProcessor[
        ResolveStorageNamespaceAction, LookupOpsResult[StorageNamespaceData]
    ]
    unregister: GlobalActionProcessor[
        UnregisterNamespaceAction, EntityOpsResult[StorageNamespaceData]
    ]

    def __init__(self, group: ProcessorGroup[StorageNamespaceData]) -> None:
        self.register = group.global_create_ops(RegisterNamespaceAction)
        self.search = group.global_search_ops(SearchStorageNamespacesAction)
        self.get_namespaces = group.global_search_ops(GetNamespacesAction)
        self.lookup = group.lookup_ops(ResolveStorageNamespaceAction)
        self.unregister = group.global_purge_ops(UnregisterNamespaceAction)
