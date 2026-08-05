from __future__ import annotations

from typing import Any, override

from ai.backend.manager.actions.registry import ProcessorRegistry
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.base import (
    CreateGlobalOpsAction,
    GetSingleEntityOpsAction,
    PurgeSingleEntityOpsAction,
    SearchGlobalOpsAction,
    UpdateSingleEntityOpsAction,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.services.app_config_allow_list.actions.admin_search import (
    AdminSearchAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.create import (
    CreateAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.get import (
    GetAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.purge import (
    PurgeAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.update import (
    UpdateAppConfigAllowListAction,
)


class AppConfigAllowListProcessors(AbstractProcessorPackage):
    """Every operation runs straight against ops, so this domain has no service."""

    create: GlobalActionProcessor[
        CreateGlobalOpsAction[Any, AppConfigAllowListData],
        CreatedEntityOpsResult[AppConfigAllowListData],
    ]
    get: SingleEntityActionProcessor[
        GetSingleEntityOpsAction[Any, AppConfigAllowListData],
        EntityOpsResult[AppConfigAllowListData],
    ]
    update: SingleEntityActionProcessor[
        UpdateSingleEntityOpsAction[Any, AppConfigAllowListData],
        EntityOpsResult[AppConfigAllowListData],
    ]
    purge: SingleEntityActionProcessor[
        PurgeSingleEntityOpsAction[Any, AppConfigAllowListData],
        EntityOpsResult[AppConfigAllowListData],
    ]
    admin_search: GlobalActionProcessor[
        SearchGlobalOpsAction[Any, AppConfigAllowListData],
        BatchOpsResult[AppConfigAllowListData],
    ]

    def __init__(self, registry: ProcessorRegistry[AppConfigAllowListData]) -> None:
        p = registry.group()
        self.create = p.global_create_ops()
        self.get = p.single_get_ops()
        self.update = p.single_update_ops()
        self.purge = p.single_purge_ops()
        self.admin_search = p.global_search_ops()

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigAllowListAction.spec(),
            GetAppConfigAllowListAction.spec(),
            AdminSearchAppConfigAllowListAction.spec(),
            UpdateAppConfigAllowListAction.spec(),
            PurgeAppConfigAllowListAction.spec(),
        ]
