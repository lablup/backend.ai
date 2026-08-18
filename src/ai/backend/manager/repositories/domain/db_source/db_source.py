from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainRow).where(DomainRow.name == domain_name)
            row = await db_sess.scalar(query)
            if row is None:
                raise DomainNotFound(f"Domain '{domain_name}' not found")
            return row.to_data()

    async def get_domain_id_by_name(self, name: DomainName) -> DomainID:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(DomainRow.id).where(DomainRow.name == name)
            domain_id = await db_sess.scalar(query)
            if domain_id is None:
                raise DomainNotFound(f"Domain '{name}' not found")
            return domain_id
