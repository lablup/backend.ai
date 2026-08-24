from __future__ import annotations

import base64
import secrets
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Final, TypedDict

import sqlalchemy as sa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import false

from ai.backend.common import msgpack
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.defs import RESERVED_DOTFILES
from ai.backend.manager.models.base import (
    GUID,
    Base,
    SecretColumn,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_group import ResourceGroupForKeypairsRow
    from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
    from ai.backend.manager.models.user import UserRow

__all__: Sequence[str] = (
    "KEYPAIR_SECRET_KEY_CONTEXT",
    "MAXIMUM_DOTFILE_SIZE",
    "Dotfile",
    "KeyPairRow",
    "keypairs",
    "query_bootstrap_script",
    "query_owned_dotfiles",
    "verify_dotfile_name",
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
        server_default=sa.text("uuid_generate_v4()"),
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
    # dotfiles column, \x90 means empty list in msgpack
    dotfiles: Mapped[bytes] = mapped_column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    )
    bootstrap_script: Mapped[str] = mapped_column(
        "bootstrap_script", sa.String(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=""
    )

    # Relationships
    resource_policy_row: Mapped[KeyPairResourcePolicyRow] = relationship("KeyPairResourcePolicyRow")
    sgroup_for_keypairs_rows: Mapped[list[ResourceGroupForKeypairsRow]] = relationship(
        "ResourceGroupForKeypairsRow",
    )
    user_row: Mapped[UserRow] = relationship(
        "UserRow", back_populates="keypairs", foreign_keys=[user]
    )

    def to_data(self) -> KeyPairData:
        return KeyPairData(
            id=self.id,
            user_id=self.user,
            access_key=AccessKey(self.access_key),
            secret_key=self.secret_key,
            is_active=self.is_active,
            is_default=self.is_default,
            is_admin=self.is_admin,
            created_at=self.created_at,
            modified_at=self.updated_at,
            resource_policy_name=self.resource_policy,
            rate_limit=self.rate_limit,
            ssh_public_key=self.ssh_public_key,
            ssh_private_key=self.ssh_private_key,
            dotfiles=self.dotfiles if self.dotfiles else b"\x90",
            bootstrap_script=self.bootstrap_script,
            last_used=self.last_used,
            num_queries=self.num_queries,
        )


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use KeyPairRow class directly for new code.
keypairs = KeyPairRow.__table__


class Dotfile(TypedDict):
    data: str
    path: str
    perm: str


def generate_keypair() -> tuple[AccessKey, SecretKey]:
    """
    AWS-like access key and secret key generation.
    """
    ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    sk = secrets.token_urlsafe(30)
    return AccessKey(ak), SecretKey(sk)


def generate_ssh_keypair() -> tuple[str, str]:
    """
    Generate RSA keypair for SSH/SFTP connection.
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
    )
    public_key = f"{public_key.rstrip()}\n"
    private_key = f"{private_key.rstrip()}\n"
    return (public_key, private_key)


async def generate_keypair_data(key_provider_pool: KeyProviderPool) -> KeyPairSecrets:
    ak, sk = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return KeyPairSecrets(
        access_key=ak,
        secret_key=await key_provider_pool.encrypt(sk, KEYPAIR_SECRET_KEY_CONTEXT),
        ssh_public_key=pubkey,
        ssh_private_key=privkey,
    )


async def query_owned_dotfiles(
    conn: SAConnection,
    access_key: AccessKey,
) -> tuple[list[Dotfile], int]:
    query = (
        sa.select(KeyPairRow.dotfiles)
        .select_from(KeyPairRow)
        .where(KeyPairRow.access_key == access_key)
    )
    packed_dotfile = (await conn.execute(query)).scalar()
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_bootstrap_script(
    conn: SAConnection,
    access_key: AccessKey,
) -> tuple[str, int]:
    query = (
        sa.select(KeyPairRow.bootstrap_script)
        .select_from(KeyPairRow)
        .where(KeyPairRow.access_key == access_key)
    )
    script = (await conn.execute(query)).scalar()
    if script is None:
        return "", MAXIMUM_DOTFILE_SIZE
    return script, MAXIMUM_DOTFILE_SIZE - len(script)


def verify_dotfile_name(dotfile: str) -> bool:
    return dotfile not in RESERVED_DOTFILES
