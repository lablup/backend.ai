from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.base import GUID, Base


class DotfileApplicationRow(Base):
    """The dotfile an entity's sessions get for one path.

    At most one per entity and path. Removing the entity's graph node or the dotfile
    deletes the row.
    """

    __tablename__ = "dotfile_applications"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["entity_type", "entity_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            ondelete="CASCADE",
        ),
    )

    entity_type: Mapped[EntityType] = mapped_column("entity_type", sa.String(32), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column("entity_id", GUID(), primary_key=True)
    path: Mapped[str] = mapped_column("path", sa.Text, primary_key=True)
    dotfile_id: Mapped[DotfileID] = mapped_column(
        "dotfile_id",
        GUID(DotfileID),
        sa.ForeignKey("dotfiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
