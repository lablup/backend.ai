from collections.abc import Sequence
from typing import Generic

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from ...permission_controller.role_manager import RoleManager
from ..session import SessionWrapper
from ..types import InsertData, TBaseEntityData, TRow


class Creator(Generic[TRow, TBaseEntityData]):
    """
    SQLAlchemy ORM creation wrapper.
    TRow: SQLAlchemy ORM model instance type.
    TBaseEntityData: Type of the associated entity insert data.
    """

    def __init__(self, session: SessionWrapper) -> None:
        self._session = session
        self._role_manager = RoleManager()

    async def add_one(self, data: InsertData[TRow, TBaseEntityData]) -> TRow:
        """
        Add a single row to the database and map its entity to the appropriate scope.
        `data`: InsertData object containing the row and associated entity data.
        """
        self._session.db_session.add(data.row)
        await self._session.db_session.flush()
        await self._session.db_session.refresh(data.row)
        await self._map_entity_to_scope(
            entity_id=ObjectId(data.entity_data.entity_type(), data.entity_data.entity_id()),
            scope_id=data.entity_data.scope_id(),
        )
        return data.row

    async def add_many(self, data: Sequence[InsertData[TRow, TBaseEntityData]]) -> list[TRow]:
        """
        Add multiple rows to the database and map their entities to the appropriate scopes.
        `data`: Sequence of InsertData objects containing the rows and associated entity data.
        """
        rows = [data_item.row for data_item in data]
        self._session.db_session.add_all(rows)
        await self._session.db_session.flush()
        for single_data in data:
            await self._session.db_session.refresh(single_data.row)
            await self._map_entity_to_scope(
                entity_id=ObjectId(
                    single_data.entity_data.entity_type(), single_data.entity_data.entity_id()
                ),
                scope_id=single_data.entity_data.scope_id(),
            )
        return list(rows)

    async def _map_entity_to_scope(
        self,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        await self._role_manager.map_entity_to_scope(
            self._session.db_session,
            entity_id=entity_id,
            scope_id=scope_id,
        )

    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        await self._session.db_session.commit()
