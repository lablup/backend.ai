from __future__ import annotations

import base64
import secrets
from typing import TYPE_CHECKING, Any, List, Sequence, Tuple, TypedDict

import sqlalchemy as sa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import false

from ai.backend.common import msgpack
from ai.backend.common.types import AccessKey, SecretKey

if TYPE_CHECKING:
    pass

from ..defs import RESERVED_DOTFILES
from .base import (
    Base,
    ForeignKeyIDColumn,
    mapper_registry,
)

__all__: Sequence[str] = (
    "keypairs",
    "KeyPairRow",
    "Dotfile",
    "MAXIMUM_DOTFILE_SIZE",
    "query_owned_dotfiles",
    "query_bootstrap_script",
    "verify_dotfile_name",
)


MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB

keypairs = sa.Table(
    "keypairs",
    mapper_registry.metadata,
    sa.Column("user_id", sa.String(length=256), index=True),
    sa.Column("access_key", sa.String(length=20), primary_key=True),
    sa.Column("secret_key", sa.String(length=40)),
    sa.Column("is_active", sa.Boolean, index=True),
    sa.Column("is_admin", sa.Boolean, index=True, default=False, server_default=false()),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
    sa.Column("rate_limit", sa.Integer),
    sa.Column("num_queries", sa.Integer, server_default="0"),
    # SSH Keypairs.
    sa.Column("ssh_public_key", sa.Text, nullable=True),
    sa.Column("ssh_private_key", sa.Text, nullable=True),
    ForeignKeyIDColumn("user", "users.uuid", nullable=False),
    sa.Column(
        "resource_policy",
        sa.String(length=256),
        sa.ForeignKey("keypair_resource_policies.name"),
        nullable=False,
    ),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
    sa.Column(
        "bootstrap_script", sa.String(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=""
    ),
)


class KeyPairRow(Base):
    __table__ = keypairs
    sessions = relationship("SessionRow", back_populates="access_key_row")
    resource_policy_row = relationship("KeyPairResourcePolicyRow", back_populates="keypairs")
    sgroup_for_keypairs_rows = relationship(
        "ScalingGroupForKeypairsRow",
        back_populates="keypair_row",
    )

    user_row = relationship("UserRow", back_populates="keypairs", foreign_keys=keypairs.c.user)

    @property
    def mapping(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "last_used": self.last_used,
            "rate_limit": self.rate_limit,
            "num_queries": self.num_queries,
            "ssh_public_key": self.ssh_public_key,
            "ssh_private_key": self.ssh_private_key,
            "user": self.user,
            "resource_policy": self.resource_policy,
            "dotfiles": self.dotfiles,
            "bootstrap_script": self.bootstrap_script,
        }


class Dotfile(TypedDict):
    data: str
    path: str
    perm: str


def generate_keypair() -> Tuple[AccessKey, SecretKey]:
    """
    AWS-like access key and secret key generation.
    """
    ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    sk = secrets.token_urlsafe(30)
    return AccessKey(ak), SecretKey(sk)


def generate_ssh_keypair() -> Tuple[str, str]:
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


async def query_owned_dotfiles(
    conn: SAConnection,
    access_key: AccessKey,
) -> Tuple[List[Dotfile], int]:
    query = (
        sa.select([keypairs.c.dotfiles])
        .select_from(keypairs)
        .where(keypairs.c.access_key == access_key)
    )
    packed_dotfile = (await conn.execute(query)).scalar()
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_bootstrap_script(
    conn: SAConnection,
    access_key: AccessKey,
) -> Tuple[str, int]:
    query = (
        sa.select([keypairs.c.bootstrap_script])
        .select_from(keypairs)
        .where(keypairs.c.access_key == access_key)
    )
    script = (await conn.execute(query)).scalar()
    return script, MAXIMUM_DOTFILE_SIZE - len(script)


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True
