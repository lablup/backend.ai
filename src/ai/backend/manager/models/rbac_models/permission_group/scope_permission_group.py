from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.permission.types import (
    ScopeType,
)

from ...base import (
    StrEnumType,
)
from .permission_group import PermissionGroupRow


class ScopePermissionGroupRow(PermissionGroupRow):
    __mapper_args__ = {
        "polymorphic_identity": "scope_permission_groups",
    }
    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=True
    )
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=True
    )  # e.g., "project_id", "user_id" etc.
