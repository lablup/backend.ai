from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.soft_delete import SoftDeleteMixin
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class BootstrapScriptRow(SoftDeleteMixin, CreatedAtMixin, Base):
    """A bootstrap script set on an entity.

    Its content lives in ``bootstrap_script_revisions``; the latest revision is the current one.
    """

    __tablename__ = "bootstrap_scripts"

    id: Mapped[BootstrapScriptID] = mapped_column(
        "id",
        GUID(BootstrapScriptID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(sa.String(32), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)


class UserDefaultBootstrapScriptRow(Base):
    """The bootstrap script a user's sessions run when the request names none.

    At most one per user. Deleting either the user or the script deletes the row.
    """

    __tablename__ = "user_default_bootstrap_scripts"

    user_id: Mapped[UserID] = mapped_column(
        "user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        primary_key=True,
    )
    script_id: Mapped[BootstrapScriptID] = mapped_column(
        "script_id",
        GUID(BootstrapScriptID),
        sa.ForeignKey("bootstrap_scripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
