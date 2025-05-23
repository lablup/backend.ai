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

from .propagator import PropagatorEventDispatcher


def dispatch_bgtask_events(
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
