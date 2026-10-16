from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.services.session_group.actions.bulk_get import BulkGetSessionGroupsAction
from ai.backend.manager.services.session_group.actions.get import GetSessionGroupAction
from ai.backend.manager.services.session_group.actions.global_search import (
    GlobalSearchSessionGroupsAction,
)
from ai.backend.manager.services.session_group.actions.scoped_search import (
    ScopedSearchSessionGroupsAction,
)
from ai.backend.manager.services.session_group.service import SessionGroupService

__all__ = ("SessionGroupProcessors",)


class SessionGroupProcessors:
    get: SingleEntityActionProcessor[GetSessionGroupAction, EntityOpsResult[SessionGroupData]]
    # What the DataLoaders read: one READ check per session group named.
    bulk_get_ids: PartialBulkActionProcessor[BulkGetSessionGroupsAction, SessionGroupData]
    global_search: GlobalActionProcessor[
        GlobalSearchSessionGroupsAction, BatchOpsResult[SessionGroupData]
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchSessionGroupsAction, ScopedBatchOpsResult[SessionGroupData]
    ]

    def __init__(
        self,
        group: ProcessorGroup[SessionGroupData],
        service: SessionGroupService,
    ) -> None:
        self.get = group.single_entity(GetSessionGroupAction, service.get)
        self.bulk_get_ids = group.partial_bulk(BulkGetSessionGroupsAction, service.bulk_get_ids)
        self.global_search = group.global_searcher_ops(GlobalSearchSessionGroupsAction)
        self.scoped_search = group.scoped_search_ops(ScopedSearchSessionGroupsAction)
