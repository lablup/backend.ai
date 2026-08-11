from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.services.app_config_definition.actions.admin_search import (
    AdminSearchAppConfigDefinitionsAction,
)
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
)


class AppConfigDefinitionProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    create: GlobalActionProcessor[
        CreateAppConfigDefinitionAction, CreatedEntityOpsResult[AppConfigDefinitionData]
    ]
    get: SingleEntityActionProcessor[
        GetAppConfigDefinitionAction, EntityOpsResult[AppConfigDefinitionData]
    ]
    purge: GlobalActionProcessor[
        PurgeAppConfigDefinitionAction, EntityOpsResult[AppConfigDefinitionData]
    ]
    admin_search: GlobalActionProcessor[
        AdminSearchAppConfigDefinitionsAction, BatchOpsResult[AppConfigDefinitionData]
    ]

    def __init__(self, group: ProcessorGroup[AppConfigDefinitionData]) -> None:
        self.create = group.global_create_ops(CreateAppConfigDefinitionAction)
        self.get = group.single_get_ops(GetAppConfigDefinitionAction)
        self.purge = group.global_purge_ops(PurgeAppConfigDefinitionAction)
        self.admin_search = group.global_search_ops(AdminSearchAppConfigDefinitionsAction)
