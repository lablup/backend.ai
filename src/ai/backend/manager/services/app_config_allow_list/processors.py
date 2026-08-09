from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
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


class AppConfigAllowListProcessors:
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
    purge: GlobalActionProcessor[
        PurgeAppConfigAllowListAction,
        EntityOpsResult[AppConfigAllowListData],
    ]
    admin_search: GlobalActionProcessor[
        AdminSearchAppConfigAllowListAction,
        BatchOpsResult[AppConfigAllowListData],
    ]

    def __init__(self, group: ProcessorGroup[AppConfigAllowListData]) -> None:
        self.create = group.global_create_ops(CreateAppConfigAllowListAction)
        self.get = group.single_get_ops(GetAppConfigAllowListAction)
        self.update = group.single_update_ops(UpdateAppConfigAllowListAction)
        self.purge = group.global_purge_ops(PurgeAppConfigAllowListAction)
        self.admin_search = group.global_search_ops(AdminSearchAppConfigAllowListAction)
