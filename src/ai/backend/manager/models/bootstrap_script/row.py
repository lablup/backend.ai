from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import false

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.soft_delete import SoftDeleteMixin
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class BootstrapScriptRow(SoftDeleteMixin, CreatedAtMixin, Base):
    """A bootstrap script set on an entity; at most one live script per entity is the default.

    Its content lives in ``bootstrap_script_revisions``; the latest revision is the current one.
    """

    __tablename__ = "bootstrap_scripts"
    __table_args__ = (
        sa.Index(
            "uq_bootstrap_scripts_is_default",
            "entity_type",
            "entity_id",
            unique=True,
            postgresql_where=sa.text("is_default AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[BootstrapScriptID] = mapped_column(
        "id",
        GUID(BootstrapScriptID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(sa.String(32), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    is_default: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=false())
