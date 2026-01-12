from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.creator import Creator as BaseCreator
from ai.backend.manager.repositories.base.creator import CreatorResult as BaseCreatorResult
from ai.backend.manager.repositories.base.creator import CreatorSpec as BaseCreatorSpec

from .utils import insert_on_conflict_do_nothing


class RBACEntityRow(ABC):
    @abstractmethod
    def scope_id(self) -> ScopeId:
        pass

    @abstractmethod
    def entity_id(self) -> ObjectId:
        pass

    @abstractmethod
    def field_id(self) -> ObjectId | None:
        pass


TEntityRow = TypeVar("TEntityRow", bound=RBACEntityRow)


class CreatorSpec(BaseCreatorSpec[TEntityRow]):
    pass


@dataclass
class Creator(BaseCreator[TEntityRow]):
    pass


@dataclass
class CreatorResult(BaseCreatorResult[TEntityRow]):
    pass


async def execute_rbac_entity_creator(
    db_sess: SASession,
    creator: Creator[TEntityRow],
) -> CreatorResult[TEntityRow]:
    """
    Execute INSERT with RBAC-aware creator.
    - Insert the main entity row.
    - Insert associated EntityFieldRow if field-scoped.
    - Insert AssociationScopesEntitiesRow if not field-scoped.

    Args:
        db_sess: Async SQLAlchemy session.
        creator: Creator instance with RBAC context and spec.

    Returns:
        Result of the create operation.
    """
    row = creator.spec.build_row()
    db_sess.add(row)
    await db_sess.flush()
    await db_sess.refresh(row)
    field_id = row.field_id()
    scope_id = row.scope_id()
    entity_id = row.entity_id()
    if field_id is not None:
        await insert_on_conflict_do_nothing(
            db_sess,
            EntityFieldRow(
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
                field_type=field_id.entity_type,
                field_id=field_id.entity_id,
            ),
        )
    else:
        await insert_on_conflict_do_nothing(
            db_sess,
            AssociationScopesEntitiesRow(
                scope_type=scope_id.scope_type,
                scope_id=scope_id.scope_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
            ),
        )
    return CreatorResult(row=row)
