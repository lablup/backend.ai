from typing import Generic

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from ...permission_controller.role_manager import RoleManager
from ..session import SessionWrapper
from ..types import TRow, TUpdator, UpdateData


class Updator(Generic[TRow, TUpdator]):
    """
    SQLAlchemy ORM update wrapper.
    TRow: SQLAlchemy ORM model instance type.
    TUpdator: Type of the data used to update the ORM model instance.
    """

    def __init__(self, session: SessionWrapper) -> None:
        self._session = session
        self._role_manager = RoleManager.instance()

    async def update(self, data: UpdateData[TRow, TUpdator]) -> TRow:
        """
        Update the provided row with the given data.
        `data`: UpdateData object containing the row and updator data.
        """
        data.row.update_from_data(data.updator)
        await self._session.db_session.flush()
        return data.row

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

    async def _unmap_entity_from_scope(
        self,
        entity_id: ObjectId,
        scope_id: ScopeId,
    ) -> None:
        await self._role_manager.unmap_entity_from_scope(
            self._session.db_session,
            entity_id=entity_id,
            scope_id=scope_id,
        )
