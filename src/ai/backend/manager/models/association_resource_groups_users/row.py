from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import GUID, Base

__all__: Sequence[str] = ("AssociationResourceGroupsUsersRow",)


class AssociationResourceGroupsUsersRow(Base):
    __tablename__ = "association_resource_groups_users"
    __table_args__ = (sa.UniqueConstraint("resource_group_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        # Named explicitly: the naming convention would generate a 69-character name,
        # over PostgreSQL's 63-character limit.
        sa.ForeignKey(
            "scaling_groups.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_association_resource_groups_users_resource_group_id",
        ),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UserID] = mapped_column(
        "user_id",
        GUID(UserID),
        sa.ForeignKey(
            "users.uuid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="fk_association_resource_groups_users_user_id",
        ),
        index=True,
        nullable=False,
    )
