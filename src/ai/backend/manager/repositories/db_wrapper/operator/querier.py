from collections.abc import AsyncGenerator
from typing import Generic, Optional

import sqlalchemy as sa

from ..session import SessionWrapper
from ..types import TRow


class Querier(Generic[TRow]):
    """
    SQLAlchemy ORM query wrapper.
    TRow: SQLAlchemy ORM model instance type.
    """

    def __init__(self, session: SessionWrapper) -> None:
        self._session = session

    async def query_many(self, stmt: sa.sql.Select) -> list[TRow]:
        """
        Execute the provided select statement and return all matching rows.
        `stmt`: SQLAlchemy Select statement. Must be like `select(ModelClass).where(...)`

        Returns a list of ORM model instances.
        """
        result = await self._session.db_session.scalars(stmt)
        return result.all()

    async def query_one(self, stmt: sa.sql.Select) -> Optional[TRow]:
        """
        Execute the provided select statement and return a single matching row.
        `stmt`: SQLAlchemy Select statement. Must be like `select(ModelClass).where(...)`

        Returns a single ORM model instance or None if no match is found.
        """
        result = await self._session.db_session.scalar(stmt)
        return result

    async def stream(self, stmt: sa.sql.Select) -> AsyncGenerator[TRow]:
        """
        Execute the provided select statement and stream matching rows.
        `stmt`: SQLAlchemy Select statement. Must be like `select(ModelClass).where(...)`

        Yields ORM model instances.
        """
        result = await self._session.db_session.stream_scalars(stmt)
        async for row in result:
            yield row
