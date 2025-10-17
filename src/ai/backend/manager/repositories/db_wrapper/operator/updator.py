from typing import Generic

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from ...permission_controller.role_manager import RoleManager
from ..types import TUpdator, Updatable


class Updator(Generic[TUpdator]):
    """
    SQLAlchemy ORM update wrapper.
    TUpdatable: SQLAlchemy ORM model instance type that supports updates.
    TUpdator: Type of the data used to update the ORM model instance.
    """

    def __init__(self, db_session: SASession) -> None:
        self._db_session = db_session
        self._role_manager = RoleManager()

    async def update(self, row: Updatable[TUpdator], data: TUpdator) -> Updatable[TUpdator]:
        """
        Update the provided row with the given data.
        `row`: The ORM model instance to be updated.
        `data`: The data used to update the ORM model instance.
        """
        row.update_from_data(data)
        await self._db_session.flush()
        return row

    async def _map_entity_to_scope(
        self,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        await self._role_manager.map_entity_to_scope(
            self._db_session,
            entity_id=entity_id,
            scope_id=scope_id,
        )

    async def _unmap_entity_from_scope(
        self,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        await self._role_manager.unmap_entity_from_scope(
            self._db_session,
            entity_id=entity_id,
            scope_id=scope_id,
        )
