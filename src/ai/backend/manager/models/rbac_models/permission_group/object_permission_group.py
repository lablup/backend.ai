from __future__ import annotations

import sqlalchemy as sa

from .permission_group import PermissionGroupRow


class ObjectPermissionGroupRow(PermissionGroupRow):
    __mapper_args__ = {
        "polymorphic_identity": "object_permission_groups",
    }
    entity_id: str = sa.Column(
        "entity_id", sa.String(64), nullable=True
    )  # e.g., "session_id", "vfolder_id" etc.
