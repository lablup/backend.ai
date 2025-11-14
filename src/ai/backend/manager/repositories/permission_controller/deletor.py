import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, final

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class RBACEntityDeletor(ABC):
    async def delete_entity(self, db_session: SASession) -> None:
        scope_id = self.scope_id()
        entity_id = self.object_id()
        try:
            await db_session.execute(
                sa.delete(AssociationScopesEntitiesRow).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == scope_id.scope_id,
                        AssociationScopesEntitiesRow.scope_type == scope_id.scope_type,
                        AssociationScopesEntitiesRow.entity_id == entity_id,
                        AssociationScopesEntitiesRow.entity_type == entity_id.entity_type,
                    )
                )
            )
        except IntegrityError:
            log.exception(
                "failed to delete entity and scope mapping: {}, {}.",
                entity_id.to_str(),
                scope_id.to_str(),
            )

    @abstractmethod
    def scope_id(self) -> ScopeId:
        raise NotImplementedError

    @abstractmethod
    def object_id(self) -> ObjectId:
        raise NotImplementedError


TDeletedEntity = TypeVar("TDeletedEntity")


class RBACDeletor(Generic[TDeletedEntity], ABC):
    def __init__(self, rbac_entity_deletor: RBACEntityDeletor) -> None:
        self._rbac_entity_deletor = rbac_entity_deletor

    @final
    async def delete(self, db_session: SASession) -> TDeletedEntity:
        entity = await self._delete(db_session)
        await self._rbac_entity_deletor.delete_entity(db_session)
        return entity

    @abstractmethod
    async def _delete(self, db_session: SASession) -> TDeletedEntity:
        raise NotImplementedError
