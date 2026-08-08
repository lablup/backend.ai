from __future__ import annotations

from typing import override

from ai.backend.manager.actions.registry import ProcessorRegistry
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
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
        CreateAppConfigAllowListAction,
        CreatedEntityOpsResult[AppConfigAllowListData],
    ]
    get: SingleEntityActionProcessor[
        GetAppConfigAllowListAction,
        EntityOpsResult[AppConfigAllowListData],
    ]
    update: SingleEntityActionProcessor[
        UpdateAppConfigAllowListAction,
        EntityOpsResult[AppConfigAllowListData],
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigAllowListAction,
        EntityOpsResult[AppConfigAllowListData],
    ]
    admin_search: GlobalActionProcessor[
        AdminSearchAppConfigAllowListAction,
        BatchOpsResult[AppConfigAllowListData],
    ]

    def __init__(self, registry: ProcessorRegistry[AppConfigAllowListData]) -> None:
        p = registry.group()
        self.create = p.global_create_ops(CreateAppConfigAllowListAction)
        self.get = p.single_get_ops(GetAppConfigAllowListAction)
        self.update = p.single_update_ops(UpdateAppConfigAllowListAction)
        self.purge = p.single_purge_ops(PurgeAppConfigAllowListAction)
        self.admin_search = p.global_search_ops(AdminSearchAppConfigAllowListAction)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigAllowListAction.spec(),
            GetAppConfigAllowListAction.spec(),
            AdminSearchAppConfigAllowListAction.spec(),
            UpdateAppConfigAllowListAction.spec(),
            PurgeAppConfigAllowListAction.spec(),
        ]
