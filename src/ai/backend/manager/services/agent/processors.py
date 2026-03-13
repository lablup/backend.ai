from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
    GetTotalResourcesActionResult,
)
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
)
from ai.backend.manager.services.agent.actions.handle_heartbeat import (
    HandleHeartbeatAction,
    HandleHeartbeatActionResult,
)
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
    LoadContainerCountsActionResult,
)
from ai.backend.manager.services.agent.actions.mark_agent_exit import (
    MarkAgentExitAction,
    MarkAgentExitActionResult,
)
from ai.backend.manager.services.agent.actions.mark_agent_running import (
    MarkAgentRunningAction,
    MarkAgentRunningActionResult,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
)
from ai.backend.manager.services.agent.actions.remove_agent_from_images import (
    RemoveAgentFromImagesAction,
    RemoveAgentFromImagesActionResult,
)
from ai.backend.manager.services.agent.actions.remove_agent_from_images_by_canonicals import (
    RemoveAgentFromImagesByCanonicalsAction,
    RemoveAgentFromImagesByCanonicalsActionResult,
)
from ai.backend.manager.services.agent.actions.search_agents import (
    SearchAgentsAction,
    SearchAgentsActionResult,
)
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
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


class AgentProcessors(AbstractProcessorPackage):
    # Internal/system actions (no RBAC)
    sync_agent_registry: ActionProcessor[SyncAgentRegistryAction, SyncAgentRegistryActionResult]
    recalculate_usage: ActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]
    handle_heartbeat: ActionProcessor[HandleHeartbeatAction, HandleHeartbeatActionResult]
    mark_agent_exit: ActionProcessor[MarkAgentExitAction, MarkAgentExitActionResult]
    mark_agent_running: ActionProcessor[MarkAgentRunningAction, MarkAgentRunningActionResult]
    remove_agent_from_images_by_canonicals: ActionProcessor[
        RemoveAgentFromImagesByCanonicalsAction, RemoveAgentFromImagesByCanonicalsActionResult
    ]
    remove_agent_from_images: ActionProcessor[
        RemoveAgentFromImagesAction, RemoveAgentFromImagesActionResult
    ]

    # Scope actions (operate on agents within a domain)
    get_total_resources: ScopeActionProcessor[
        GetTotalResourcesAction, GetTotalResourcesActionResult
    ]
    search_agents: ScopeActionProcessor[SearchAgentsAction, SearchAgentsActionResult]
    load_container_counts: ScopeActionProcessor[
        LoadContainerCountsAction, LoadContainerCountsActionResult
    ]

    # Single-entity actions (operate on specific agents)
    get_watcher_status: SingleEntityActionProcessor[
        GetWatcherStatusAction, GetWatcherStatusActionResult
    ]
    watcher_agent_start: SingleEntityActionProcessor[
        WatcherAgentStartAction, WatcherAgentStartActionResult
    ]
    watcher_agent_restart: SingleEntityActionProcessor[
        WatcherAgentRestartAction, WatcherAgentRestartActionResult
    ]
    watcher_agent_stop: SingleEntityActionProcessor[
        WatcherAgentStopAction, WatcherAgentStopActionResult
    ]

    def __init__(
        self,
        service: AgentService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Internal/system actions (no RBAC validators)
        self.sync_agent_registry = ActionProcessor(service.sync_agent_registry, action_monitors)
        self.recalculate_usage = ActionProcessor(service.recalculate_usage, action_monitors)
        self.handle_heartbeat = ActionProcessor(service.handle_heartbeat, action_monitors)
        self.mark_agent_exit = ActionProcessor(service.mark_agent_exit, action_monitors)
        self.mark_agent_running = ActionProcessor(service.mark_agent_running, action_monitors)
        self.remove_agent_from_images_by_canonicals = ActionProcessor(
            service.remove_agent_from_images_by_canonicals, action_monitors
        )
        self.remove_agent_from_images = ActionProcessor(
            service.remove_agent_from_images, action_monitors
        )

        # Scope actions with RBAC validators
        self.get_total_resources = ScopeActionProcessor(
            service.get_total_resources, action_monitors, validators=[validators.rbac.scope]
        )
        self.search_agents = ScopeActionProcessor(
            service.search_agents, action_monitors, validators=[validators.rbac.scope]
        )
        self.load_container_counts = ScopeActionProcessor(
            service.load_container_counts, action_monitors, validators=[validators.rbac.scope]
        )

        # Single-entity actions with RBAC validators
        self.get_watcher_status = SingleEntityActionProcessor(
            service.get_watcher_status, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.watcher_agent_start = SingleEntityActionProcessor(
            service.watcher_agent_start, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.watcher_agent_restart = SingleEntityActionProcessor(
            service.watcher_agent_restart,
            action_monitors,
            validators=[validators.rbac.single_entity],
        )
        self.watcher_agent_stop = SingleEntityActionProcessor(
            service.watcher_agent_stop, action_monitors, validators=[validators.rbac.single_entity]
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            SyncAgentRegistryAction.spec(),
            GetWatcherStatusAction.spec(),
            WatcherAgentStartAction.spec(),
            WatcherAgentRestartAction.spec(),
            WatcherAgentStopAction.spec(),
            RecalculateUsageAction.spec(),
            GetTotalResourcesAction.spec(),
            HandleHeartbeatAction.spec(),
            RemoveAgentFromImagesAction.spec(),
            RemoveAgentFromImagesByCanonicalsAction.spec(),
            SearchAgentsAction.spec(),
            LoadContainerCountsAction.spec(),
        ]
