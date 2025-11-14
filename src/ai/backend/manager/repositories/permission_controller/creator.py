import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

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


@dataclass
class RBACEntityCreateInput:
    scope_id: ScopeId
    object_id: ObjectId


TEntityCreateInput = TypeVar("TEntityCreateInput")
TCreatedEntity = TypeVar("TCreatedEntity")


class RBACEntityCreator(Generic[TEntityCreateInput, TCreatedEntity], ABC):
    async def create_entity(
        self,
        db_session: SASession,
        input: TEntityCreateInput,
        rbac_input: RBACEntityCreateInput,
    ) -> TCreatedEntity:
        result = await self._create_entity(db_session, input)
        await self._create_rbac_entity(db_session, rbac_input)
        return result

    @abstractmethod
    async def _create_entity(
        self,
        db_session: SASession,
        input: TEntityCreateInput,
    ) -> TCreatedEntity:
        raise NotImplementedError

    async def _create_rbac_entity(
        self,
        db_session: SASession,
        rbac_input: RBACEntityCreateInput,
    ) -> None:
        scope_id = rbac_input.scope_id
        entity_id = rbac_input.object_id
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
