from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.permission_group import (
    PermissionGroupCreator,
    PermissionGroupData,
    PermissionGroupExtendedData,
)
from ai.backend.manager.data.permission.types import (
    ScopeType,
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

    from .object_permission import ObjectPermissionRow
    from .permission import PermissionRow


def _get_role_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.rbac_models.role import RoleRow

    return RoleRow.id == foreign(PermissionGroupRow.role_id)


def _get_association_scopes_entities_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.rbac_models.association_scopes_entities import (
        AssociationScopesEntitiesRow,
    )

    return PermissionGroupRow.scope_id == foreign(AssociationScopesEntitiesRow.scope_id)


def _get_permission_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

    return PermissionGroupRow.id == foreign(PermissionRow.permission_group_id)


def _get_object_permission_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.rbac_models.permission.object_permission import (
        ObjectPermissionRow,
    )

    return PermissionGroupRow.id == foreign(ObjectPermissionRow.permission_group_id)


class PermissionGroupRow(Base):  # type: ignore[misc]
    __tablename__ = "permission_groups"
    __table_args__ = (
        sa.Index("ix_id_role_id_scope_id", "id", "role_id", "scope_id"),
        sa.UniqueConstraint(
            "role_id",
            "scope_type",
            "scope_id",
            name="uq_permission_groups_role_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    role_id: Mapped[uuid.UUID] = mapped_column("role_id", GUID, nullable=False)
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: Mapped[str] = mapped_column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.

    role_row: Mapped[RoleRow | None] = relationship(
        "RoleRow",
        back_populates="permission_group_rows",
        primaryjoin=_get_role_join_condition,
        viewonly=True,
    )
    mapped_entities: Mapped[list[AssociationScopesEntitiesRow]] = relationship(
        "AssociationScopesEntitiesRow",
        primaryjoin=_get_association_scopes_entities_join_condition,
        viewonly=True,
    )
    permission_rows: Mapped[list[PermissionRow]] = relationship(
        "PermissionRow",
        back_populates="permission_group_row",
        primaryjoin=_get_permission_join_condition,
        passive_deletes=True,
    )
    object_permission_rows: Mapped[list[ObjectPermissionRow]] = relationship(
        "ObjectPermissionRow",
        back_populates="permission_group_row",
        primaryjoin=_get_object_permission_join_condition,
        passive_deletes=True,
    )

    def parsed_scope_id(self) -> ScopeId:
        return ScopeId(scope_type=self.scope_type, scope_id=self.scope_id)

    @classmethod
    def from_input(cls, input: PermissionGroupCreator) -> Self:
        return cls(
            role_id=input.role_id,
            scope_type=input.scope_id.scope_type,
            scope_id=input.scope_id.scope_id,
        )

    def to_data(self) -> PermissionGroupData:
        return PermissionGroupData(
            id=self.id,
            role_id=self.role_id,
            scope_id=ScopeId(scope_type=self.scope_type, scope_id=self.scope_id),
        )

    def to_extended_data(self) -> PermissionGroupExtendedData:
        return PermissionGroupExtendedData(
            id=self.id,
            role_id=self.role_id,
            scope_id=ScopeId(scope_type=self.scope_type, scope_id=self.scope_id),
            permissions=[permission.to_data() for permission in self.permission_rows],
        )
