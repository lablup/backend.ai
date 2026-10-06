from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.models.base import GUID, Base

log = StructuredLogger(logging.getLogger(__spec__.name))

__all__: Sequence[str] = ("AssociationContainerRegistriesGroupsRow",)


class AssociationContainerRegistriesGroupsRow(Base):
    __tablename__ = "association_container_registries_groups"
    __table_args__ = (
        sa.Index(
            "uq_project_image_commit_target",
            "group_id",
            unique=True,
            postgresql_where=sa.text("is_image_commit_target"),
        ),
        sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    registry_id: Mapped[ContainerRegistryID] = mapped_column(
        "registry_id",
        GUID(ContainerRegistryID),
        # Named explicitly: the naming convention would generate a 75-character name,
        # over PostgreSQL's 63-character limit.
        sa.ForeignKey(
            "container_registries.id",
            ondelete="CASCADE",
            name="fk_association_container_registries_groups_registry_id",
        ),
        nullable=False,
    )
    group_id: Mapped[ProjectID] = mapped_column(
        "group_id",
        GUID(ProjectID),
        sa.ForeignKey(
            "groups.id",
            ondelete="CASCADE",
            name="fk_association_container_registries_groups_group_id",
        ),
        nullable=False,
    )

    is_image_commit_target: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False, server_default=sa.false()
    )
