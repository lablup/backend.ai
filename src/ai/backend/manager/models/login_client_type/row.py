from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

if TYPE_CHECKING:
    from ai.backend.manager.data.login_client_type.types import LoginClientTypeData

__all__ = ("LoginClientTypeRow",)


class LoginClientTypeRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "login_client_types"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)

    def to_dataclass(self) -> LoginClientTypeData:
        from ai.backend.manager.data.login_client_type.types import LoginClientTypeData

        return LoginClientTypeData(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            modified_at=self.updated_at,
        )
