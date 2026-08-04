"""Junction table recording which images are installed on which agents."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.types import ImageID
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("AgentImageRow",)


class AgentImageRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """One row per (agent, image) installation."""

    __tablename__ = "agent_images"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID(), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    agent_id: Mapped[str] = mapped_column("agent_id", sa.String(length=64), nullable=False)
    image_id: Mapped[ImageID] = mapped_column("image_id", GUID(ImageID), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint("agent_id", "image_id", name="uq_agent_images_agent_id_image_id"),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_images_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["images.id"],
            name="fk_agent_images_image_id_images",
            ondelete="CASCADE",
        ),
        sa.Index("ix_agent_images_image_id", "image_id"),
    )
