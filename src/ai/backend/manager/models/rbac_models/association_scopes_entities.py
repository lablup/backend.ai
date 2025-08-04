from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import (
    relationship,
)

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.scope_entity_mapping import ScopeEntityMappingData

from ..base import (
    Base,
    IDColumn,
)

if TYPE_CHECKING:
    from .scope_permission import ScopePermissionRow


class AssociationScopesEntitiesRow(Base):
    __tablename__ = "association_scopes_entities"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("scope_id", "entity_id", name="uq_scope_id_entity_id"),
    )

    id: uuid.UUID = IDColumn()

    scope_type: str = sa.Column(
        "scope_type",
        sa.String(32),
        nullable=False,
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id",
        sa.String(64),
        nullable=False,
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
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

    scope_permission_row: ScopePermissionRow = relationship(
        "ScopePermissionRow",
        back_populates="mapped_entity_rows",
        primaryjoin="ScopePermissionRow.scope_id == foreign(AssociationScopesEntitiesRow.scope_id)",
    )

    def object_id(self) -> ObjectId:
        """
        Convert the association to a tuple of ScopeId and ObjectId.
        """
        return ObjectId(entity_type=self.entity_type, entity_id=self.entity_id)

    def to_data(self) -> ScopeEntityMappingData:
        """
        Convert the association to ScopeEntityMappingData.
        """
        return ScopeEntityMappingData(
            id=self.id,
            scope_id=ScopeId(scope_type=self.scope_type, scope_id=self.scope_id),
            entity_id=self.object_id(),
        )
