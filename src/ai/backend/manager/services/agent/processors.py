from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
    GetWatcherStatusActionResult,
)
from ai.backend.manager.services.agent.actions.recalculate_usage import (
    RecalculateUsageAction,
    RecalculateUsageActionResult,
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


class AgentProcessors:
    sync_agent_registry: ActionProcessor[SyncAgentRegistryAction, SyncAgentRegistryActionResult]
    get_watcher_status: ActionProcessor[GetWatcherStatusAction, GetWatcherStatusActionResult]
    watcher_agent_start: ActionProcessor[WatcherAgentStartAction, WatcherAgentStartActionResult]
    watcher_agent_restart: ActionProcessor[
        WatcherAgentRestartAction, WatcherAgentRestartActionResult
    ]
    watcher_agent_stop: ActionProcessor[WatcherAgentStopAction, WatcherAgentStopActionResult]
    recalculate_usage: ActionProcessor[RecalculateUsageAction, RecalculateUsageActionResult]

    def __init__(self, service: AgentService, action_monitors: list[ActionMonitor]) -> None:
        self.sync_agent_registry = ActionProcessor(service.sync_agent_registry, action_monitors)
        self.get_watcher_status = ActionProcessor(service.get_watcher_status, action_monitors)
        self.watcher_agent_start = ActionProcessor(service.watcher_agent_start, action_monitors)
        self.watcher_agent_restart = ActionProcessor(service.watcher_agent_restart, action_monitors)
        self.watcher_agent_stop = ActionProcessor(service.watcher_agent_stop, action_monitors)
        self.recalculate_usage = ActionProcessor(service.recalculate_usage, action_monitors)
