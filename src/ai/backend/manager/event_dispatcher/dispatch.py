from dataclasses import dataclass

from ai.backend.common.events.bgtask import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
    BgtaskUpdatedEvent,
)
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
)
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.reporter import AbstractEventReporter, EventProtocol, EventReportArgs
from ai.backend.manager.event_dispatcher.propagator import PropagatorEventDispatcher

from ..models.event_log import EventLogRow
from ..models.utils import ExtendedAsyncSAEngine


def _dispatch_bgtask_events(
    event_dispatcher: EventDispatcher,
    dispatcher: PropagatorEventDispatcher,
) -> None:
    """
    Register event dispatchers for background task events.
    """
    event_dispatcher.subscribe(BgtaskUpdatedEvent, None, dispatcher.propagate_event)
    event_dispatcher.subscribe(BgtaskDoneEvent, None, dispatcher.propagate_event)
    event_dispatcher.subscribe(
        BgtaskPartialSuccessEvent,
        None,
        dispatcher.propagate_event,
    )
    event_dispatcher.subscribe(BgtaskCancelledEvent, None, dispatcher.propagate_event)
    event_dispatcher.subscribe(BgtaskFailedEvent, None, dispatcher.propagate_event)


@dataclass
class DispatcherArgs:
    event_hub: EventHub


class Dispatchers:
    propagator_dispatcher: PropagatorEventDispatcher

    def __init__(self, args: DispatcherArgs) -> None:
        """
        Initialize the Dispatchers with the given arguments.
        """
        self.propagator_dispatcher = PropagatorEventDispatcher(args.event_hub)

    def dispatch(self, event_dispatcher: EventDispatcher) -> None:
        """
        Dispatch events to the appropriate dispatcher.
        """
        _dispatch_bgtask_events(event_dispatcher, self.propagator_dispatcher)


class EventLogger(AbstractEventReporter):
    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db

    async def report(
        self,
        event: EventProtocol,
        args: EventReportArgs = EventReportArgs.nop(),
    ) -> None:
        async with self._db.begin_session() as session:
            event_log = EventLogRow.from_event(event)
            session.add(event_log)
            await session.flush()
