import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

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


TRow = TypeVar("TRow")


@dataclass
class CreatorResult(Generic[TRow]):
    row: TRow
    scope_map_rows: list[AssociationScopesEntitiesRow]


class RBACEntityCreator(Generic[TRow], ABC):
    @abstractmethod
    def row(self) -> TRow:
        pass

    @abstractmethod
    def rbac_scope_inputs(self) -> list[RBACEntityCreateInput]:
        pass


async def execute_cretor[TRow](
    db_sess: SASession,
    creator: RBACEntityCreator[TRow],
) -> CreatorResult[TRow]:
    created_row = creator.row()
    db_sess.add(created_row)
    await db_sess.flush()

    created_scope_map_rows: list[AssociationScopesEntitiesRow] = []
    for scope_input in creator.rbac_scope_inputs():
        scope_id = scope_input.scope_id
        entity_id = scope_input.object_id
        scope_mapper = AssociationScopesEntitiesCreateInput(
            scope_id=scope_id,
            object_id=entity_id,
        )
        map_row = AssociationScopesEntitiesRow.from_input(scope_mapper)
        try:
            db_sess.add(map_row)
            await db_sess.flush()
            created_scope_map_rows.append(map_row)
        except IntegrityError:
            log.exception(
                "entity and scope mapping already exists (entity id: {}, scope id: {}). Skipping.",
                entity_id.to_str(),
                scope_id.to_str(),
            )

    return CreatorResult(
        row=created_row,
        scope_map_rows=created_scope_map_rows,
    )
