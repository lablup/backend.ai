from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: Sequence[str] = ("AssociationContainerRegistriesGroupsRow",)


class AssociationContainerRegistriesGroupsRow(Base):
    __tablename__ = "association_container_registries_groups"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    registry_id: Mapped[uuid.UUID] = mapped_column(
        "registry_id",
        GUID,
        nullable=False,
    )
    group_id: Mapped[ProjectID] = mapped_column(
        "group_id",
        GUID(ProjectID),
        nullable=False,
    )
