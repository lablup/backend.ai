from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.global_bulk_upsert import (
    GlobalBulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)


class AppConfigFragmentProcessors:
    """Fragment writes and reads, none of them admin-only except the ``public`` write.

    A write is gated by the fragment's FK to ``app_config_allow_list``: an insert with no
    allow-list row for its ``(config_name, scope_type)`` is rejected as write-not-allowed.
    An allow-listed user may therefore manage their own fragment without admin rights.
    """

    bulk_upsert: ScopeActionProcessor[
        BulkUpsertAppConfigFragmentsAction, EntitiesOpsResult[AppConfigFragmentData]
    ]
    global_bulk_upsert: GlobalActionProcessor[
        GlobalBulkUpsertAppConfigFragmentsAction, EntitiesOpsResult[AppConfigFragmentData]
    ]
    get: SingleEntityActionProcessor[
        GetAppConfigFragmentAction, EntityOpsResult[AppConfigFragmentData]
    ]
    admin_search: GlobalActionProcessor[
        AdminSearchAppConfigFragmentAction, BatchOpsResult[AppConfigFragmentData]
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchAppConfigFragmentAction, ScopedBatchOpsResult[AppConfigFragmentData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, EntityOpsResult[AppConfigFragmentData]
    ]
    bulk_purge: BulkActionProcessor[
        BulkPurgeAppConfigFragmentAction, BulkOpsResult[AppConfigFragmentData]
    ]

    def __init__(self, group: ProcessorGroup[AppConfigFragmentData]) -> None:
        self.bulk_upsert = group.entity_atomic_upsert_ops(BulkUpsertAppConfigFragmentsAction)
        self.global_bulk_upsert = group.global_atomic_upsert_ops(
            GlobalBulkUpsertAppConfigFragmentsAction
        )
        self.get = group.single_get_ops(GetAppConfigFragmentAction)
        self.admin_search = group.global_search_ops(AdminSearchAppConfigFragmentAction)
        self.scoped_search = group.scope_search_ops(ScopedSearchAppConfigFragmentAction)
        self.purge = group.entity_purge_ops(PurgeAppConfigFragmentAction)
        self.bulk_purge = group.entity_partial_bulk_purge_ops(BulkPurgeAppConfigFragmentAction)
