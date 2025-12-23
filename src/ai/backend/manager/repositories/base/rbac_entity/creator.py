from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.permission.id import (
    ObjectId,
    ScopeId,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)


class RBACEntityRow(ABC):
    @abstractmethod
    def parsed_object_id(self) -> ObjectId:
        pass


TEntityRow = TypeVar("TEntityRow", bound=RBACEntityRow)


class CreatorSpec(ABC, Generic[TEntityRow]):
    """Abstract base class defining a row to insert.

    Implementations specify what to create by providing:
    - A build_row() method that returns the ORM instance to insert
    """

    @abstractmethod
    def build_row(self) -> TEntityRow:
        """Build ORM row instance to insert.

        Returns:
            An ORM model instance to be inserted
        """
        raise NotImplementedError


@dataclass
class Creator(Generic[TEntityRow]):
    """Bundles RBAC-aware creator spec for insert operations.

    Attributes:
        spec: CreatorSpec implementation defining what to create.
        rbac_context: RBAC context for the creation operation.
    """

    spec: CreatorSpec[TEntityRow]
    scope_id: ScopeId


@dataclass
class CreatorResult(Generic[TEntityRow]):
    """Result of executing a create operation."""

    row: TEntityRow


async def execute_creator(
    db_sess: SASession,
    creator: Creator[TEntityRow],
) -> CreatorResult[TEntityRow]:
    """Execute INSERT with RBAC-aware creator.

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
    scope_id = creator.scope_id
    object_id = row.parsed_object_id()
    db_sess.add(
        AssociationScopesEntitiesRow(
            scope_type=scope_id.scope_type,
            scope_id=scope_id.scope_id,
            entity_type=object_id.entity_type,
            entity_id=object_id.entity_id,
        )
    )
    return CreatorResult(row=row)
