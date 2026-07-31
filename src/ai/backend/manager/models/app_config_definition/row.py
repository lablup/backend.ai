from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("AppConfigDefinitionRow",)


class AppConfigDefinitionRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    """One registered ``config_name`` (admin-managed).

    Purging a row cascades to its allow-list entries (``ON DELETE CASCADE``) and,
    through them, to their fragments.
    """

    __tablename__ = "app_config_definitions"

    id: Mapped[AppConfigDefinitionID] = mapped_column(
        "id",
        GUID(AppConfigDefinitionID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    config_name: Mapped[str] = mapped_column(
        "config_name", sa.String(length=128), nullable=False, unique=True
    )

    def to_data(self) -> AppConfigDefinitionData:
        return AppConfigDefinitionData(
            id=self.id,
            config_name=self.config_name,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
