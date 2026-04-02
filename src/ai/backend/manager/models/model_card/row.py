from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.base import GUID, Base, PydanticColumn
from ai.backend.manager.models.model_card.types import MinResourceSpec

__all__ = ("ModelCardRow",)


class ModelCardRow(Base):  # type: ignore[misc]
    __tablename__ = "model_cards"

    __table_args__ = (
        sa.UniqueConstraint("name", "domain", "project", name="uq_model_cards_name_domain_project"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=512), nullable=False)
    vfolder: Mapped[uuid.UUID] = mapped_column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project: Mapped[uuid.UUID] = mapped_column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    creator: Mapped[uuid.UUID] = mapped_column(
        "creator",
        GUID,
        sa.ForeignKey("users.uuid", ondelete="RESTRICT"),
        nullable=False,
    )

    author: Mapped[str | None] = mapped_column("author", sa.String(length=256), nullable=True)
    title: Mapped[str | None] = mapped_column("title", sa.String(length=512), nullable=True)
    model_version: Mapped[str | None] = mapped_column(
        "model_version", sa.String(length=64), nullable=True
    )
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    task: Mapped[str | None] = mapped_column("task", sa.String(length=128), nullable=True)
    category: Mapped[str | None] = mapped_column("category", sa.String(length=128), nullable=True)
    architecture: Mapped[str | None] = mapped_column(
        "architecture", sa.String(length=128), nullable=True
    )
    framework: Mapped[list[str]] = mapped_column(
        "framework", pgsql.ARRAY(sa.String), nullable=False, server_default="{}"
    )
    label: Mapped[list[str]] = mapped_column(
        "label", pgsql.ARRAY(sa.String), nullable=False, server_default="{}"
    )
    license: Mapped[str | None] = mapped_column("license", sa.String(length=128), nullable=True)
    min_resource: Mapped[MinResourceSpec | None] = mapped_column(
        "min_resource", PydanticColumn(MinResourceSpec), nullable=True
    )
    readme: Mapped[str | None] = mapped_column("readme", sa.Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.now(),
    )

    def to_data(self) -> ModelCardData:
        return ModelCardData(
            id=self.id,
            name=self.name,
            vfolder_id=self.vfolder,
            domain=self.domain,
            project_id=self.project,
            creator_id=self.creator,
            author=self.author,
            title=self.title,
            model_version=self.model_version,
            description=self.description,
            task=self.task,
            category=self.category,
            architecture=self.architecture,
            framework=self.framework or [],
            label=self.label or [],
            license=self.license,
            min_resource=self.min_resource.slots if self.min_resource else None,
            readme=self.readme,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
