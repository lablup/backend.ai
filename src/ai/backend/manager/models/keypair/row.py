from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Final

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import false

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.base import (
    GUID,
    Base,
    SecretColumn,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.secret.types import SecretValue

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_group.row import ResourceGroupForKeypairsRow

__all__: Sequence[str] = (
    "KEYPAIR_SECRET_KEY_CONTEXT",
    "MAXIMUM_DOTFILE_SIZE",
    "KeyPairRow",
    "keypairs",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB

# The associated data every secret key is encrypted and decrypted under.
KEYPAIR_SECRET_KEY_CONTEXT: Final[str] = "keypairs.secret_key"


class KeyPairRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "keypairs"
    __table_args__ = (
        # Partial unique index: at most one keypair per user may have is_default = true.
        sa.Index(
            "uq_keypairs_is_default",
            "user",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
    )

    id: Mapped[KeyPairID] = mapped_column(
        "id",
        GUID(KeyPairID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v7()"),
    )
    access_key: Mapped[AccessKey] = mapped_column(
        "access_key", sa.String(length=20), primary_key=True
    )
    secret_key: Mapped[SecretValue] = mapped_column(
        "secret_key", SecretColumn(KEYPAIR_SECRET_KEY_CONTEXT), nullable=False
    )
    is_active: Mapped[bool] = mapped_column("is_active", sa.Boolean, index=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(
        "is_admin", sa.Boolean, index=True, default=False, server_default=false(), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        "is_default", sa.Boolean, nullable=False, default=False, server_default=false()
    )
    last_used: Mapped[datetime | None] = mapped_column(
        "last_used", sa.DateTime(timezone=True), nullable=True
    )
    rate_limit: Mapped[int] = mapped_column(
        "rate_limit", sa.Integer, nullable=False, server_default=sa.text("10000")
    )
    num_queries: Mapped[int] = mapped_column(
        "num_queries", sa.Integer, server_default="0", nullable=False
    )
    # SSH Keypairs.
    ssh_public_key: Mapped[str | None] = mapped_column("ssh_public_key", sa.Text, nullable=True)
    ssh_private_key: Mapped[str | None] = mapped_column("ssh_private_key", sa.Text, nullable=True)
    user: Mapped[UserID] = mapped_column(
        "user", GUID(UserID), sa.ForeignKey("users.uuid"), nullable=False
    )
    resource_policy: Mapped[str] = mapped_column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("keypair_resource_policies.name"),
        nullable=False,
    )

    # Relationships
    sgroup_for_keypairs_rows: Mapped[list[ResourceGroupForKeypairsRow]] = relationship(
        "ResourceGroupForKeypairsRow",
    )


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use KeyPairRow class directly for new code.
keypairs = KeyPairRow.__table__
