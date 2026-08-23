from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
    AppConfigFragmentData,
)
from ai.backend.manager.services.app_config.actions.allow_list.admin_search import (
    AdminSearchAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config.actions.allow_list.bulk_get import (
    BulkGetAppConfigAllowListsAction,
)
from ai.backend.manager.services.app_config.actions.allow_list.create import (
    CreateAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config.actions.allow_list.get import (
    GetAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config.actions.allow_list.purge import (
    PurgeAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config.actions.allow_list.update import (
    UpdateAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config.actions.definition.admin_search import (
    AdminSearchAppConfigDefinitionsAction,
)
from ai.backend.manager.services.app_config.actions.definition.bulk_get import (
    BulkGetAppConfigDefinitionsAction,
)
from ai.backend.manager.services.app_config.actions.definition.create import (
    CreateAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config.actions.definition.get import (
    GetAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config.actions.definition.purge import (
    PurgeAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config.actions.fragment.admin_search import (
    AdminSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_get import (
    BulkGetAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.actions.fragment.get import (
    GetAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.global_bulk_upsert import (
    GlobalBulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.actions.fragment.purge import (
    PurgeAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.fragment.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
)
from ai.backend.manager.services.app_config.actions.search import (
    AnonymousSearchAppConfigsAction,
    SearchAppConfigsAction,
    SearchAppConfigsActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors:
    """The merged read, and the three tables it is computed from.

    One domain rather than four, because none of the three stands on its own: a
    definition registers a name, an allow-list entry decides who may fill it and in what
    order, and a fragment holds a value under that design.

    Only the merged read keeps a service; every other operation runs straight against
    ops. A fragment write splits by who answers for it — an owned one at that owner's
    scope, a public one behind the SUPERADMIN gate.
    """

    search_app_configs: ScopeActionProcessor[SearchAppConfigsAction, SearchAppConfigsActionResult]
    anonymous_search_app_configs: ScopeActionProcessor[
        AnonymousSearchAppConfigsAction, SearchAppConfigsActionResult
    ]

    definition_global_create: GlobalActionProcessor[
        CreateAppConfigDefinitionAction, CreatedEntityOpsResult[AppConfigDefinitionData]
    ]
    definition_get: SingleEntityActionProcessor[
        GetAppConfigDefinitionAction, EntityOpsResult[AppConfigDefinitionData]
    ]
    definition_bulk_get: PartialBulkActionProcessor[
        BulkGetAppConfigDefinitionsAction, AppConfigDefinitionData
    ]
    definition_purge: SingleEntityActionProcessor[
        PurgeAppConfigDefinitionAction, EntityOpsResult[AppConfigDefinitionData]
    ]
    definition_global_search: GlobalActionProcessor[
        AdminSearchAppConfigDefinitionsAction, BatchOpsResult[AppConfigDefinitionData]
    ]

    allow_list_global_create: GlobalActionProcessor[
        CreateAppConfigAllowListAction, CreatedEntityOpsResult[AppConfigAllowListData]
    ]
    allow_list_get: SingleEntityActionProcessor[
        GetAppConfigAllowListAction, EntityOpsResult[AppConfigAllowListData]
    ]
    allow_list_bulk_get: PartialBulkActionProcessor[
        BulkGetAppConfigAllowListsAction, AppConfigAllowListData
    ]
    allow_list_update: SingleEntityActionProcessor[
        UpdateAppConfigAllowListAction, EntityOpsResult[AppConfigAllowListData]
    ]
    allow_list_purge: SingleEntityActionProcessor[
        PurgeAppConfigAllowListAction, EntityOpsResult[AppConfigAllowListData]
    ]
    allow_list_global_search: GlobalActionProcessor[
        AdminSearchAppConfigAllowListAction, BatchOpsResult[AppConfigAllowListData]
    ]

    fragment_bulk_upsert: ScopeActionProcessor[
        BulkUpsertAppConfigFragmentsAction, EntitiesOpsResult[AppConfigFragmentData]
    ]
    fragment_global_bulk_upsert: GlobalActionProcessor[
        GlobalBulkUpsertAppConfigFragmentsAction, EntitiesOpsResult[AppConfigFragmentData]
    ]
    fragment_get: SingleEntityActionProcessor[
        GetAppConfigFragmentAction, EntityOpsResult[AppConfigFragmentData]
    ]
    fragment_bulk_get: PartialBulkActionProcessor[
        BulkGetAppConfigFragmentsAction, AppConfigFragmentData
    ]
    fragment_admin_search: GlobalActionProcessor[
        AdminSearchAppConfigFragmentAction, BatchOpsResult[AppConfigFragmentData]
    ]
    fragment_scoped_search: ScopeActionProcessor[
        ScopedSearchAppConfigFragmentAction, ScopedBatchOpsResult[AppConfigFragmentData]
    ]
    fragment_purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, EntityOpsResult[AppConfigFragmentData]
    ]
    fragment_bulk_purge: PartialBulkActionProcessor[
        BulkPurgeAppConfigFragmentAction, AppConfigFragmentData
    ]

    def __init__(
        self,
        # No ops on the merged read, so this group's data type is unused.
        merged_group: ProcessorGroup[Any],
        definition_group: ProcessorGroup[AppConfigDefinitionData],
        allow_list_group: ProcessorGroup[AppConfigAllowListData],
        fragment_group: ProcessorGroup[AppConfigFragmentData],
        service: AppConfigService,
    ) -> None:
        self.search_app_configs = merged_group.scope(
            SearchAppConfigsAction, service.search_app_configs
        )
        self.anonymous_search_app_configs = merged_group.anonymous_scope(
            AnonymousSearchAppConfigsAction, service.anonymous_search_app_configs
        )

        self.definition_global_create = definition_group.global_create_ops(
            CreateAppConfigDefinitionAction
        )
        self.definition_get = definition_group.single_get_ops(GetAppConfigDefinitionAction)
        self.definition_bulk_get = definition_group.partial_bulk_get_ops(
            BulkGetAppConfigDefinitionsAction
        )
        self.definition_purge = definition_group.entity_purge_ops(PurgeAppConfigDefinitionAction)
        self.definition_global_search = definition_group.global_search_ops(
            AdminSearchAppConfigDefinitionsAction
        )

        self.allow_list_global_create = allow_list_group.global_create_ops(
            CreateAppConfigAllowListAction
        )
        self.allow_list_get = allow_list_group.single_get_ops(GetAppConfigAllowListAction)
        self.allow_list_bulk_get = allow_list_group.partial_bulk_get_ops(
            BulkGetAppConfigAllowListsAction
        )
        self.allow_list_update = allow_list_group.single_update_ops(UpdateAppConfigAllowListAction)
        self.allow_list_purge = allow_list_group.entity_purge_ops(PurgeAppConfigAllowListAction)
        self.allow_list_global_search = allow_list_group.global_search_ops(
            AdminSearchAppConfigAllowListAction
        )

        self.fragment_bulk_upsert = fragment_group.entity_atomic_upsert_ops(
            BulkUpsertAppConfigFragmentsAction
        )
        self.fragment_global_bulk_upsert = fragment_group.global_atomic_upsert_ops(
            GlobalBulkUpsertAppConfigFragmentsAction
        )
        self.fragment_get = fragment_group.single_get_ops(GetAppConfigFragmentAction)
        self.fragment_bulk_get = fragment_group.partial_bulk_get_ops(
            BulkGetAppConfigFragmentsAction
        )
        self.fragment_admin_search = fragment_group.global_search_ops(
            AdminSearchAppConfigFragmentAction
        )
        self.fragment_scoped_search = fragment_group.scope_search_ops(
            ScopedSearchAppConfigFragmentAction
        )
        self.fragment_purge = fragment_group.entity_purge_ops(PurgeAppConfigFragmentAction)
        self.fragment_bulk_purge = fragment_group.entity_partial_bulk_purge_ops(
            BulkPurgeAppConfigFragmentAction
        )
