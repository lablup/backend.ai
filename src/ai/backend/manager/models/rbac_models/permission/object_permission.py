from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.rbac_models.association_scopes_entities import (
        AssociationScopesEntitiesRow,
    )
    from ai.backend.manager.models.rbac_models.role import RoleRow

    from .permission_group import PermissionGroupRow


def _get_role_join_condition():
    from ai.backend.manager.models.rbac_models.role import RoleRow

    return RoleRow.id == foreign(ObjectPermissionRow.role_id)


def _get_scope_association_join_condition():
    from ai.backend.manager.models.rbac_models.association_scopes_entities import (
        AssociationScopesEntitiesRow,
    )

    return sa.and_(
        ObjectPermissionRow.entity_type == foreign(AssociationScopesEntitiesRow.entity_type),
        ObjectPermissionRow.entity_id == foreign(AssociationScopesEntitiesRow.entity_id),
    )


def _get_permission_group_join_condition():
    from ai.backend.manager.models.rbac_models.permission.permission_group import (
        PermissionGroupRow,
    )

    return PermissionGroupRow.id == foreign(ObjectPermissionRow.permission_group_id)


class ObjectPermissionRow(Base):
    __tablename__ = "object_permissions"
    __table_args__ = (
        sa.Index("ix_id_role_id_entity_id", "id", "role_id", "entity_id"),
        sa.UniqueConstraint(
            "role_id",
            "entity_type",
            "entity_id",
            "operation",
            name="uq_object_permissions_role_entity_op",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column("role_id", GUID, nullable=False)
    permission_group_id: Mapped[uuid.UUID] = mapped_column(
        "permission_group_id",
        GUID,
        sa.ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    entity_id: Mapped[str] = mapped_column(
        "entity_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.
    operation: Mapped[OperationType] = mapped_column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    role_row: Mapped[RoleRow | None] = relationship(
        "RoleRow",
        back_populates="object_permission_rows",
        primaryjoin=_get_role_join_condition,
        viewonly=True,
    )
    permission_group_row: Mapped[PermissionGroupRow] = relationship(
        "PermissionGroupRow",
        back_populates="object_permission_rows",
        primaryjoin=_get_permission_group_join_condition,
    )
    scope_association_rows: Mapped[list[AssociationScopesEntitiesRow]] = relationship(
        "AssociationScopesEntitiesRow",
        primaryjoin=_get_scope_association_join_condition,
        viewonly=True,
        uselist=True,
    )

    def object_id(self) -> ObjectId:
        return ObjectId(entity_type=self.entity_type, entity_id=self.entity_id)

    @classmethod
    def from_sa_row(cls, row: sa.engine.Row) -> Self:
        return cls(
            id=row.id,
            role_id=row.role_id,
            permission_group_id=row.permission_group_id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            operation=row.operation,
        )

    def to_data(self) -> ObjectPermissionData:
        return ObjectPermissionData(
            id=self.id,
            role_id=self.role_id,
            permission_group_id=self.permission_group_id,
            object_id=self.object_id(),
            operation=self.operation,
        )
