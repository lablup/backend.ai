from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.data.login_client_type.types import LoginClientTypeSearchResult
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("LoginClientTypeAdminRepository",)


class LoginClientTypeAdminRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def search(
        self,
        querier: BatchQuerier,
    ) -> LoginClientTypeSearchResult:
        """Search all login client types with pagination and filters (admin, no scope)."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(LoginClientTypeRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.LoginClientTypeRow.to_dataclass() for row in result.rows]

            return LoginClientTypeSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
