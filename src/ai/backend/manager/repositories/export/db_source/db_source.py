"""Export DB source for database operations."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import TYPE_CHECKING, Any

from ai.backend.manager.repositories.base.export import (
    StreamingExportQuery,
    execute_streaming_export,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ExportDBSource",)


class ExportDBSource:
    """DB source for export streaming operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def stream_export(
        self,
        query: StreamingExportQuery,
    ) -> AsyncIterator[Sequence[Sequence[Any]]]:
        """Execute streaming export.

        Args:
            query: Export query containing fields, conditions, orders, and limits

        Yields:
            Partitions of row values (each row in query.fields order)
        """
        async for partition in execute_streaming_export(self._db, query):
            yield partition
