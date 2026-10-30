from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, EntityOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.services.system_session_environ.actions.bulk_get import (
    BulkGetSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.actions.create import (
    CreateSystemSessionEnvironAction,
    CreateSystemSessionEnvironActionResult,
)
from ai.backend.manager.services.system_session_environ.actions.delete import (
    DeleteSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.global_search import (
    GlobalSearchSystemSessionEnvironsAction,
)
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
    PublicListSystemSessionEnvironValueSourcesActionResult,
)
from ai.backend.manager.services.system_session_environ.actions.purge import (
    PurgeSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.restore import (
    RestoreSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.actions.update import (
    UpdateSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.service import SystemSessionEnvironService

__all__ = ("SystemSessionEnvironProcessors",)


class SystemSessionEnvironProcessors:
    global_search: GlobalActionProcessor[
        GlobalSearchSystemSessionEnvironsAction,
        BatchOpsResult[SystemSessionEnvironData],
    ]
    public_list_value_sources: PublicActionProcessor[
        PublicListSystemSessionEnvironValueSourcesAction,
        PublicListSystemSessionEnvironValueSourcesActionResult,
    ]
    create: ScopeActionProcessor[
        CreateSystemSessionEnvironAction, CreateSystemSessionEnvironActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateSystemSessionEnvironAction, EntityOpsResult[SystemSessionEnvironData]
    ]
    delete: SingleEntityActionProcessor[
        DeleteSystemSessionEnvironAction, EntityOpsResult[SystemSessionEnvironData]
    ]
    restore: SingleEntityActionProcessor[
        RestoreSystemSessionEnvironAction, EntityOpsResult[SystemSessionEnvironData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeSystemSessionEnvironAction, EntityOpsResult[SystemSessionEnvironData]
    ]
    bulk_get_ids: PartialBulkActionProcessor[
        BulkGetSystemSessionEnvironsAction, SystemSessionEnvironData
    ]

    def __init__(self, group: ProcessorGroup[Any], service: SystemSessionEnvironService) -> None:
        self.global_search = group.global_searcher_ops(GlobalSearchSystemSessionEnvironsAction)
        self.public_list_value_sources = group.public(
            PublicListSystemSessionEnvironValueSourcesAction, service.public_list_value_sources
        )
        self.create = group.scope(CreateSystemSessionEnvironAction, service.create)
        self.update = group.single_update_ops(UpdateSystemSessionEnvironAction)
        self.delete = group.single_delete_ops(DeleteSystemSessionEnvironAction)
        self.restore = group.single_restore_ops(RestoreSystemSessionEnvironAction)
        self.purge = group.entity_purge_ops(PurgeSystemSessionEnvironAction)
        self.bulk_get_ids = group.partial_bulk_get_ops(BulkGetSystemSessionEnvironsAction)
