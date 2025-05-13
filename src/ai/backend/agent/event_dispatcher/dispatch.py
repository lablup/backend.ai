
from dataclasses import dataclass

from ai.backend.agent.manager import Agent
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.volume import DoVolumeMountEvent, DoVolumeUnmountEvent


class AgentDispatcher:
    _agent: Agent
    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    


@dataclass
class DispatcherArgs:
    agent: Agent


class Dispatchers:
    _agent_dispatcher: AgentDispatcher

    def __init__(self, args: DispatcherArgs) -> None:
        """
        Initialize the Dispatchers with the given arguments.
        """
        self._agent_dispatcher = AgentDispatcher(args.agent)
    
    def _dispatch_agent_events(
        self,
        event_dispatcher: EventDispatcher,
    ) -> None:
        """
        Register event dispatchers for agent events.
        """
        # Register agent events here
        event_dispatcher.subscribe(DoVolumeMountEvent, self, handle_volume_mount, name="ag.volume.mount")
        event_dispatcher.subscribe(DoVolumeUnmountEvent, self, handle_volume_umount, name="ag.volume.umount")


    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        """
        Dispatch events to the appropriate dispatcher.
        """
        _dispatch_bgtask_events(event_dispatcher, self.propagator_dispatcher)
