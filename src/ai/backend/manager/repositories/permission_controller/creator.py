import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, final

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class RBACEntityCreator(ABC):
    async def create_entity(self, db_session: SASession) -> None:
        scope_id = self.scope_id()
        entity_id = self.object_id()
        creator = AssociationScopesEntitiesCreateInput(
            scope_id=scope_id,
            object_id=entity_id,
        )
        try:
            await db_session.execute(
                sa.insert(AssociationScopesEntitiesRow).values(creator.fields_to_store())
            )
        except IntegrityError:
            log.exception(
                "entity and scope mapping already exists: {}, {}. Skipping.",
                entity_id.to_str(),
                scope_id.to_str(),
            )

    @abstractmethod
    def scope_id(self) -> ScopeId:
        raise NotImplementedError

    @abstractmethod
    def object_id(self) -> ObjectId:
        raise NotImplementedError


TCreatedEntity = TypeVar("TCreatedEntity")


class RBACCreator(Generic[TCreatedEntity], ABC):
    def __init__(self, rbac_entity_creator: RBACEntityCreator) -> None:
        self._rbac_entity_creator = rbac_entity_creator

    @final
    async def create(self, db_session: SASession) -> TCreatedEntity:
        entity = await self._create(db_session)
        await self._rbac_entity_creator.create_entity(db_session)
        return entity

    @abstractmethod
    async def _create(self, db_session: SASession) -> TCreatedEntity:
        raise NotImplementedError
