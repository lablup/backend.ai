from ai.backend.common.events.reporter import AbstractEventReporter, EventProtocol, EventReportArgs

from ..models.event_log import EventLogRow
from ..models.utils import ExtendedAsyncSAEngine


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
