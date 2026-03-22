import datetime as dt
import logging
from datetime import UTC, datetime

import sqlalchemy as sa
from dateutil.relativedelta import relativedelta

from ai.backend.common import validators as tx
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.event_types.log.anycast import DoLogCleanupEvent
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LogCleanupEventHandler:
    _etcd: AsyncEtcd
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        etcd: AsyncEtcd,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._etcd = etcd
        self._db = db

    async def handle_log_cleanup(
        self,
        _context: None,
        _source: AgentId,
        _event: DoLogCleanupEvent,
    ) -> None:
        raw_lifetime = await self._etcd.get("config/logs/error/retention")
        if raw_lifetime is None:
            raw_lifetime = "90d"
        lifetime: dt.timedelta | relativedelta
        try:
            lifetime = tx.TimeDuration().check(raw_lifetime)
        except ValueError:
            lifetime = dt.timedelta(days=90)
            log.warning(
                "Failed to parse the error log retention period ({}) read from etcd; "
                "falling back to 90 days",
                raw_lifetime,
            )
        boundary = datetime.now(UTC) - lifetime
        async with self._db.begin() as conn:
            query = sa.delete(error_logs).where(error_logs.c.created_at < boundary)
            result = await conn.execute(query)
            if result.rowcount > 0:
                log.info("Cleaned up {} log(s) filed before {}", result.rowcount, boundary)
