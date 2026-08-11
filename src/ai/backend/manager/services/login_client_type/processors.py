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
    """The catalog's reads, open to every authenticated user."""

    get: PublicActionProcessor[GetLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]]
    search: PublicActionProcessor[SearchLoginClientTypesAction, BatchOpsResult[LoginClientTypeData]]

    def __init__(self, group: ProcessorGroup[LoginClientTypeData]) -> None:
        self.get = group.public_get_ops(GetLoginClientTypeAction)
        self.search = group.public_search_ops(SearchLoginClientTypesAction)


class LoginClientTypeAdminProcessors:
    """The catalog's writes, behind the SUPERADMIN gate."""

    create: GlobalActionProcessor[
        CreateLoginClientTypeAction, CreatedEntityOpsResult[LoginClientTypeData]
    ]
    update: GlobalActionProcessor[UpdateLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]]
    purge: GlobalActionProcessor[PurgeLoginClientTypeAction, EntityOpsResult[LoginClientTypeData]]

    def __init__(self, group: ProcessorGroup[LoginClientTypeData]) -> None:
        self.create = group.global_create_ops(CreateLoginClientTypeAction)
        self.update = group.global_update_ops(UpdateLoginClientTypeAction)
        self.purge = group.global_purge_ops(PurgeLoginClientTypeAction)
