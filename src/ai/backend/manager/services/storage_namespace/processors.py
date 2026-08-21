from __future__ import annotations

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.actions.lookup import (
    LookupStorageNamespaceAction,
)
from ai.backend.manager.services.storage_namespace.actions.register import RegisterNamespaceAction
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

    global_register: GlobalActionProcessor[
        RegisterNamespaceAction, CreatedEntityOpsResult[StorageNamespaceData]
    ]
    global_search: GlobalActionProcessor[
        SearchStorageNamespacesAction, BatchOpsResult[StorageNamespaceData]
    ]
    global_get_namespaces: GlobalActionProcessor[
        GetNamespacesAction, BatchOpsResult[StorageNamespaceData]
    ]
    lookup: LookupActionProcessor[LookupStorageNamespaceAction, LookupOpsResult[StorageNamespaceID]]
    unregister: SingleEntityActionProcessor[
        UnregisterNamespaceAction, EntityOpsResult[StorageNamespaceData]
    ]

    def __init__(self, group: ProcessorGroup[StorageNamespaceData]) -> None:
        self.global_register = group.global_create_ops(RegisterNamespaceAction)
        self.global_search = group.global_search_ops(SearchStorageNamespacesAction)
        self.global_get_namespaces = group.global_search_ops(GetNamespacesAction)
        self.lookup = group.lookup_ops(LookupStorageNamespaceAction)
        self.unregister = group.entity_purge_ops(UnregisterNamespaceAction)
