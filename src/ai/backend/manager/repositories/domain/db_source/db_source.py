from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.domain.types import DomainSearchResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DomainDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_domain(self, domain_name: str) -> DomainData:
        """Get a single domain by name.

        Args:
            domain_name: The name of the domain to retrieve.

        Returns:
            DomainData for the domain.

        Raises:
            DomainNotFound: If the domain does not exist.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DomainRow).where(DomainRow.name == domain_name)
            row = await db_sess.scalar(query)
            if row is None:
                raise DomainNotFound(f"Domain '{domain_name}' not found")
            return row.to_data()

    async def search_domains(self, querier: BatchQuerier) -> DomainSearchResult:
        """Search all domains with pagination and filters.

        Args:
            querier: Contains conditions, orders, and pagination.

        Returns:
            DomainSearchResult with items, total_count, and pagination flags.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DomainRow)
            result = await execute_batch_querier(db_sess, query, querier)

            items = [row.DomainRow.to_data() for row in result.rows]

            return DomainSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
