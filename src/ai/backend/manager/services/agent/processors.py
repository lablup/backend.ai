from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AGENT_RESOURCE_FIELD_TYPE
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BulkLookupOpsResult,
    LookupOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.services.agent.actions.bulk_get import BulkGetAgentsAction
from ai.backend.manager.services.agent.actions.bulk_load_container_counts import (
    BulkLoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.bulk_lookup import BulkLookupAgentsAction
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
    GetTotalResourcesActionResult,
)
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
)
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
    LoadContainerCountsActionResult,
)
from ai.backend.manager.services.agent.actions.lookup import LookupAgentAction
from ai.backend.manager.services.agent.actions.lookup_resource_owner import (
    LookupAgentResourceOwnerAction,
    LookupBulkAgentResourceOwnerAction,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.agent.actions.scoped_search_resources import (
    ScopedSearchAgentResourcesAction,
)
from ai.backend.manager.services.agent.actions.search_agents import (
    SearchAgentsAction,
    SearchAgentsActionResult,
)
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)
from ai.backend.manager.services.agent.actions.update_resource_group import (
    UpdateAgentResourceGroupAction,
    UpdateAgentResourceGroupActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
    WatcherAgentRestartActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import (
    WatcherAgentStartAction,
    WatcherAgentStartActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
    WatcherAgentStopActionResult,
)
from ai.backend.manager.services.agent.service import AgentService


class AgentProcessors:
    lookup: LookupActionProcessor[LookupAgentAction, LookupOpsResult[AgentUUID]]
    bulk_lookup: BulkLookupActionProcessor[
        BulkLookupAgentsAction, BulkLookupOpsResult[AgentId, AgentUUID]
    ]
    bulk_get: PartialBulkActionProcessor[BulkGetAgentsAction, AgentData]
    bulk_load_container_counts: PartialBulkActionProcessor[BulkLoadContainerCountsAction, int]
    scoped_search_resources: BulkActionProcessor[
        ScopedSearchAgentResourcesAction, ScopedFieldsOpsResult[AgentResourceData]
    ]
    sync_agent_registry: GlobalActionProcessor[
        SyncAgentRegistryAction, SyncAgentRegistryActionResult
    ]
    get_watcher_status: GlobalActionProcessor[GetWatcherStatusAction, GetWatcherStatusActionResult]
    watcher_agent_start: GlobalActionProcessor[
        WatcherAgentStartAction, WatcherAgentStartActionResult
    ]
    watcher_agent_restart: GlobalActionProcessor[
        WatcherAgentRestartAction, WatcherAgentRestartActionResult
    ]
    watcher_agent_stop: GlobalActionProcessor[WatcherAgentStopAction, WatcherAgentStopActionResult]
    recalculate_usage: GlobalActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]
    update_resource_group: GlobalActionProcessor[
        UpdateAgentResourceGroupAction, UpdateAgentResourceGroupActionResult
    ]
    get_total_resources: GlobalActionProcessor[
        GetTotalResourcesAction, GetTotalResourcesActionResult
    ]
    search_agents: GlobalActionProcessor[SearchAgentsAction, SearchAgentsActionResult]
    load_container_counts: GlobalActionProcessor[
        LoadContainerCountsAction, LoadContainerCountsActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[AgentData],
        service: AgentService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupAgentAction)
        self.bulk_lookup = group.public_bulk_lookup_ops(BulkLookupAgentsAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetAgentsAction)
        self.bulk_load_container_counts = group.partial_bulk(
            BulkLoadContainerCountsAction, service.bulk_load_container_counts
        )
        resources: LookupFieldGroup[AgentResourceData] = group.field_group(
            FieldGroupMeta(AGENT_RESOURCE_FIELD_TYPE),
            AgentResourceData,
            LookupAgentResourceOwnerAction,
            LookupBulkAgentResourceOwnerAction,
        )
        self.scoped_search_resources = resources.atomic_bulk_scoped_search_ops(
            ScopedSearchAgentResourcesAction
        )
        self.sync_agent_registry = group.global_scope(
            SyncAgentRegistryAction, service.sync_agent_registry
        )
        self.get_watcher_status = group.global_scope(
            GetWatcherStatusAction, service.get_watcher_status
        )
        self.watcher_agent_start = group.global_scope(
            WatcherAgentStartAction, service.watcher_agent_start
        )
        self.watcher_agent_restart = group.global_scope(
            WatcherAgentRestartAction, service.watcher_agent_restart
        )
        self.watcher_agent_stop = group.global_scope(
            WatcherAgentStopAction, service.watcher_agent_stop
        )
        self.recalculate_usage = group.global_scope(
            RecalculateUsageAction, service.recalculate_usage
        )
        self.update_resource_group = group.global_scope(
            UpdateAgentResourceGroupAction, service.update_resource_group
        )
        self.get_total_resources = group.global_scope(
            GetTotalResourcesAction, service.get_total_resources
        )
        self.search_agents = group.global_scope(SearchAgentsAction, service.search_agents)
        self.load_container_counts = group.global_scope(
            LoadContainerCountsAction, service.load_container_counts
        )
