from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.services.login_client_type.actions.bulk_get import (
    BulkGetLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.partial_bulk_purge import (
    PartialBulkPurgeLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.partial_bulk_update import (
    PartialBulkUpdateLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.purge import (
    PurgeLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.scoped_search import (
    ScopedSearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)


class LoginClientTypeProcessors:
    """The catalog is read in public, where every account holds READ; its writes are not.

    One class per domain: the gate belongs to the operation, and a separate admin
    class would state it twice.
    """

    get: SingleEntityActionProcessor[GetLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]]
    bulk_get: PartialBulkActionProcessor[BulkGetLoginClientTypesAction, LoginClientTypeData]
    scoped_search: ScopeActionProcessor[
        ScopedSearchLoginClientTypesAction, ScopedBatchOpsResult[LoginClientTypeData]
    ]
    global_create: GlobalActionProcessor[
        CreateLoginClientTypeAction, CreatedEntityOpsResult[LoginClientTypeData]
    ]
    update: SingleEntityActionProcessor[
        UpdateLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]
    ]
    partial_bulk_update: PartialBulkActionProcessor[
        PartialBulkUpdateLoginClientTypesAction, LoginClientTypeData
    ]
    partial_bulk_purge: PartialBulkActionProcessor[
        PartialBulkPurgeLoginClientTypesAction, LoginClientTypeData
    ]

    def __init__(self, group: ProcessorGroup[LoginClientTypeData]) -> None:
        self.get = group.single_get_ops(GetLoginClientTypeAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetLoginClientTypesAction)
        self.scoped_search = group.scoped_search_ops(ScopedSearchLoginClientTypesAction)
        self.global_create = group.global_create_ops(CreateLoginClientTypeAction)
        self.update = group.single_update_ops(UpdateLoginClientTypeAction)
        self.purge = group.entity_purge_ops(PurgeLoginClientTypeAction)
        self.partial_bulk_update = group.partial_bulk_update_ops(
            PartialBulkUpdateLoginClientTypesAction
        )
        self.partial_bulk_purge = group.entity_partial_bulk_purge_ops(
            PartialBulkPurgeLoginClientTypesAction
        )
