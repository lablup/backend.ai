from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType

from ..base import (
    Base,
    IDColumn,
    StrEnumType,
)


class AssociationScopesEntitiesRow(Base):
    __tablename__ = "association_scopes_entities"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("scope_type", "scope_id", "entity_id", name="uq_scope_id_entity_id"),
    )

    id: uuid.UUID = IDColumn()

    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: str = sa.Column(
        "scope_id",
        sa.String(64),
        nullable=False,
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    entity_id: str = sa.Column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )
    registered_at: datetime = sa.Column(
        "registered_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    def object_id(self) -> ObjectId:
        """
        Convert the association to a tuple of ScopeId and ObjectId.
        """
        return ObjectId(entity_type=self.entity_type, entity_id=self.entity_id)

    def parsed_scope_id(self) -> ScopeId:
        """
        Convert the association to a ScopeId.
        """
        return ScopeId(scope_type=self.scope_type, scope_id=self.scope_id)

    def to_data(self) -> AssociationScopesEntitiesData:
        """
        Convert the association to a data object.
        """
        return AssociationScopesEntitiesData(
            id=self.id,
            scope_id=ScopeId(
                scope_type=self.scope_type,
                scope_id=self.scope_id,
            ),
            object_id=self.object_id(),
        )
