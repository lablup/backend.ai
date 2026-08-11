"""Junction table recording which images are installed on which agents."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("AgentInstalledImageRow",)


class AgentInstalledImageRow(CreatedAtMixin, Base):
    """One row per (agent, image) installation.

    Composite primary key: (agent_id, image_id). All writes go through
    natural-key upsert and condition-based deletes, so no surrogate key
    is needed.
    """

    __tablename__ = "agent_installed_images"

    agent_id: Mapped[AgentId] = mapped_column("agent_id", sa.String(length=64), primary_key=True)
    image_id: Mapped[ImageID] = mapped_column("image_id", GUID(ImageID), primary_key=True)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_installed_images_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["images.id"],
            name="fk_agent_installed_images_image_id_images",
            ondelete="CASCADE",
        ),
        sa.Index("ix_agent_installed_images_image_id", "image_id"),
    )
