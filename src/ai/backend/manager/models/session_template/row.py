from __future__ import annotations

import enum
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import GUID, Base, EnumType

__all__: Sequence[str] = (
    "TemplateType",
    "SessionTemplateRow",
)


class TemplateType(enum.StrEnum):
    TASK = "task"
    CLUSTER = "cluster"


class SessionTemplateRow(Base):
    __tablename__ = "session_templates"

    id: Mapped[SessionTemplateID] = mapped_column(
        "id",
        GUID(SessionTemplateID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
        nullable=False,
    )
    is_active: Mapped[bool | None] = mapped_column("is_active", sa.Boolean, default=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), sa.ForeignKey("domains.name"), nullable=False
    )
    group_id: Mapped[ProjectID | None] = mapped_column(
        "group_id", GUID(ProjectID), sa.ForeignKey("groups.id"), nullable=True
    )
    user_uuid: Mapped[UserID] = mapped_column(
        "user_uuid", GUID(UserID), sa.ForeignKey("users.uuid"), index=True, nullable=False
    )
    type: Mapped[TemplateType] = mapped_column(
        "type", EnumType(TemplateType), nullable=False, server_default="TASK", index=True
    )
    name: Mapped[str | None] = mapped_column("name", sa.String(length=128), nullable=True)
    template: Mapped[dict[str, Any]] = mapped_column("template", pgsql.JSONB(), nullable=False)
