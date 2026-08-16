from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
)
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.purge import (
    PurgeLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    SearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)


class LoginClientTypeProcessors:
    """The catalog's reads are open to every authenticated user; its writes are not.

    One class per domain: which gate an operation carries is a property of that
    operation, and splitting the admin half into its own class states it twice --
    once in the class name and once in the factory that wires it.
    """

    public_get: PublicSingleEntityActionProcessor[
        GetLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]
    ]
    public_search: PublicActionProcessor[
        SearchLoginClientTypesAction, BatchOpsResult[LoginClientTypeData]
    ]
    global_create: GlobalActionProcessor[
        CreateLoginClientTypeAction, CreatedEntityOpsResult[LoginClientTypeData]
    ]
    global_update: GlobalActionProcessor[
        UpdateLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]
    ]
    global_purge: GlobalActionProcessor[
        PurgeLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]
    ]

    def __init__(self, group: ProcessorGroup[LoginClientTypeData]) -> None:
        self.public_get = group.public_get_ops(GetLoginClientTypeAction)
        self.public_search = group.public_search_ops(SearchLoginClientTypesAction)
        self.global_create = group.global_create_ops(CreateLoginClientTypeAction)
        self.global_update = group.global_update_ops(UpdateLoginClientTypeAction)
        self.global_purge = group.global_purge_ops(PurgeLoginClientTypeAction)
