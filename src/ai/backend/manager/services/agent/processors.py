from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
    sync_agent_registry: ActionProcessor[SyncAgentRegistryAction, SyncAgentRegistryActionResult]
    get_watcher_status: ActionProcessor[GetWatcherStatusAction, GetWatcherStatusActionResult]
    watcher_agent_start: ActionProcessor[WatcherAgentStartAction, WatcherAgentStartActionResult]
    watcher_agent_restart: ActionProcessor[
        WatcherAgentRestartAction, WatcherAgentRestartActionResult
    ]
    watcher_agent_stop: ActionProcessor[WatcherAgentStopAction, WatcherAgentStopActionResult]
    recalculate_usage: ActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]
    get_total_resources: ActionProcessor[GetTotalResourcesAction, GetTotalResourcesActionResult]
    handle_heartbeat: ActionProcessor[HandleHeartbeatAction, HandleHeartbeatActionResult]
    mark_agent_exit: ActionProcessor[MarkAgentExitAction, MarkAgentExitActionResult]
    mark_agent_running: ActionProcessor[MarkAgentRunningAction, MarkAgentRunningActionResult]
    remove_agent_from_images: ActionProcessor[
        RemoveAgentFromImagesAction, RemoveAgentFromImagesActionResult
    ]

    def __init__(self, service: AgentService, action_monitors: list[ActionMonitor]) -> None:
        self.sync_agent_registry = ActionProcessor(service.sync_agent_registry, action_monitors)
        self.get_watcher_status = ActionProcessor(service.get_watcher_status, action_monitors)
        self.watcher_agent_start = ActionProcessor(service.watcher_agent_start, action_monitors)
        self.watcher_agent_restart = ActionProcessor(service.watcher_agent_restart, action_monitors)
        self.watcher_agent_stop = ActionProcessor(service.watcher_agent_stop, action_monitors)
        self.recalculate_usage = ActionProcessor(service.recalculate_usage, action_monitors)
        self.get_total_resources = ActionProcessor(service.get_total_resources, action_monitors)
        self.handle_heartbeat = ActionProcessor(service.handle_heartbeat, action_monitors)
        self.mark_agent_exit = ActionProcessor(service.mark_agent_exit, action_monitors)
        self.mark_agent_running = ActionProcessor(service.mark_agent_running, action_monitors)
        self.remove_agent_from_images = ActionProcessor(
            service.remove_agent_from_images, action_monitors
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
        ]
