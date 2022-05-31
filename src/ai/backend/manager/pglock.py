from __future__ import annotations

from typing import Any, AsyncContextManager

from ai.backend.common.lock import AbstractDistributedLock

from .models.utils import ExtendedAsyncSAEngine
from .defs import LockID


class PgAdvisoryLock(AbstractDistributedLock):

    _lock_ctx: AsyncContextManager | None

    def __init__(self, db: ExtendedAsyncSAEngine, lock_id: LockID) -> None:
        self.db = db
        self.lock_id = lock_id
        self._lock_ctx = None

    async def __aenter__(self) -> Any:
        self._lock_ctx = self.db.advisory_lock(self.lock_id)
        await self._lock_ctx.__aenter__()

    async def __aexit__(self, *exc_info) -> bool | None:
        assert self._lock_ctx is not None
        try:
            return await self._lock_ctx.__aexit__(*exc_info)
        finally:
            self._lock_ctx = None
