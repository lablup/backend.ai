from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any

from ai.backend.common.lock import AbstractDistributedLock

from .defs import LockID
from .errors import LockContextNotInitializedError
from .models.utils import ExtendedAsyncSAEngine


class PgAdvisoryLock(AbstractDistributedLock):
    _lock_ctx: AbstractAsyncContextManager[Any] | None

    def __init__(self, db: ExtendedAsyncSAEngine, lock_id: LockID) -> None:
        self.db = db
        self.lock_id = lock_id
        self._lock_ctx = None

    async def __aenter__(self) -> Any:
        self._lock_ctx = self.db.advisory_lock(self.lock_id)
        await self._lock_ctx.__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if self._lock_ctx is None:
            raise LockContextNotInitializedError("Lock context is not initialized")
        try:
            result: bool | None = await self._lock_ctx.__aexit__(exc_type, exc_val, exc_tb)
            return result
        finally:
            self._lock_ctx = None
