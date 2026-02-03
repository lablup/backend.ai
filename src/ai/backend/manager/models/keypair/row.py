from __future__ import annotations

import base64
import os
import secrets
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Self, TypedDict

import sqlalchemy as sa
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA256
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.sql.expression import false

from ai.backend.common import msgpack
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.keypair.types import GeneratedKeyPairData, KeyPairCreator, KeyPairData
from ai.backend.manager.defs import RESERVED_DOTFILES
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
    from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.user import UserRow

__all__: Sequence[str] = (
    "MAXIMUM_DOTFILE_SIZE",
    "Dotfile",
    "KeyPairRow",
    "keypairs",
    "query_bootstrap_script",
    "query_owned_dotfiles",
    "verify_dotfile_name",
)


MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB


# Defined for avoiding circular import
def _get_session_row_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.session import SessionRow

    return KeyPairRow.access_key == foreign(SessionRow.access_key)


class KeyPairRow(Base):  # type: ignore[misc]
    __tablename__ = "keypairs"

    user_id: Mapped[str | None] = mapped_column("user_id", sa.String(length=256), index=True)
    access_key: Mapped[str] = mapped_column("access_key", sa.String(length=20), primary_key=True)
    secret_key: Mapped[str | None] = mapped_column("secret_key", sa.String(length=40))
    is_active: Mapped[bool | None] = mapped_column("is_active", sa.Boolean, index=True)
    is_admin: Mapped[bool | None] = mapped_column(
        "is_admin", sa.Boolean, index=True, default=False, server_default=false()
    )
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )
    last_used: Mapped[datetime | None] = mapped_column(
        "last_used", sa.DateTime(timezone=True), nullable=True
    )
    rate_limit: Mapped[int | None] = mapped_column("rate_limit", sa.Integer)
    num_queries: Mapped[int | None] = mapped_column("num_queries", sa.Integer, server_default="0")
    # SSH Keypairs.
    ssh_public_key: Mapped[str | None] = mapped_column("ssh_public_key", sa.Text, nullable=True)
    ssh_private_key: Mapped[str | None] = mapped_column("ssh_private_key", sa.Text, nullable=True)
    user: Mapped[uuid.UUID] = mapped_column(
        "user", GUID, sa.ForeignKey("users.uuid"), nullable=False
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
    sessions: Mapped[list[SessionRow]] = relationship(
        "SessionRow",
        primaryjoin=_get_session_row_join_condition,
        foreign_keys="SessionRow.access_key",
        back_populates="access_key_row",
    )
    resource_policy_row: Mapped[KeyPairResourcePolicyRow] = relationship(
        "KeyPairResourcePolicyRow", back_populates="keypairs"
    )
    sgroup_for_keypairs_rows: Mapped[list[ScalingGroupForKeypairsRow]] = relationship(
        "ScalingGroupForKeypairsRow",
        back_populates="keypair_row",
    )
    user_row: Mapped[UserRow] = relationship(
        "UserRow", back_populates="keypairs", foreign_keys=[user]
    )

    @property
    def mapping(self) -> dict[str, object]:
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

    @classmethod
    def from_creator(
        cls,
        creator: KeyPairCreator,
        generated_data: GeneratedKeyPairData,
        user_id: uuid.UUID,
        email: str,
    ) -> Self:
        return cls(
            user_id=email,
            user=user_id,
            access_key=generated_data.access_key,
            secret_key=generated_data.secret_key,
            is_active=creator.is_active,
            is_admin=creator.is_admin,
            resource_policy=creator.resource_policy,
            rate_limit=creator.rate_limit,
            num_queries=0,
            ssh_public_key=generated_data.ssh_public_key,
            ssh_private_key=generated_data.ssh_private_key,
        )

    def to_data(self) -> KeyPairData:
        if self.secret_key is None:
            raise ValueError("secret_key is required for KeyPairData")
        return KeyPairData(
            user_id=self.user,
            access_key=AccessKey(self.access_key),
            secret_key=SecretKey(self.secret_key),
            is_active=self.is_active if self.is_active is not None else True,
            is_admin=self.is_admin if self.is_admin is not None else False,
            created_at=self.created_at,
            modified_at=self.modified_at,
            resource_policy_name=self.resource_policy,
            rate_limit=self.rate_limit if self.rate_limit is not None else 0,
            ssh_public_key=self.ssh_public_key,
            ssh_private_key=self.ssh_private_key,
            dotfiles=self.dotfiles if self.dotfiles else b"\x90",
            bootstrap_script=self.bootstrap_script,
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


def prepare_new_keypair(user_email: str, creator: KeyPairCreator) -> dict[str, object]:
    ak, sk = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return {
        "user_id": user_email,
        "access_key": ak,
        "secret_key": sk,
        "is_active": creator.is_active,
        "is_admin": creator.is_admin,
        "resource_policy": creator.resource_policy,
        "rate_limit": creator.rate_limit,
        "num_queries": 0,
        "ssh_public_key": pubkey,
        "ssh_private_key": privkey,
    }


def generate_keypair_data() -> GeneratedKeyPairData:
    ak, sk = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return GeneratedKeyPairData(
        access_key=ak,
        secret_key=sk,
        ssh_public_key=pubkey,
        ssh_private_key=privkey,
    )


def _generate_random_bytes_to_verify_keypairs() -> bytes:
    # Check if the keys match by signing and verifying a test message
    return os.urandom(32)


def _check_rsa_keypair(private_key: rsa.RSAPrivateKey, public_key: rsa.RSAPublicKey) -> None:
    test_message = _generate_random_bytes_to_verify_keypairs()
    signature = private_key.sign(test_message, PKCS1v15(), SHA256())
    public_key.verify(signature, test_message, PKCS1v15(), SHA256())


def _check_ecdsa_keypair(
    private_key: ec.EllipticCurvePrivateKey, public_key: ec.EllipticCurvePublicKey
) -> None:
    test_message = _generate_random_bytes_to_verify_keypairs()
    signature = private_key.sign(test_message, ec.ECDSA(SHA256()))
    public_key.verify(signature, test_message, ec.ECDSA(SHA256()))


def _check_ed25519_keypair(
    private_key: ed25519.Ed25519PrivateKey, public_key: ed25519.Ed25519PublicKey
) -> None:
    test_message = _generate_random_bytes_to_verify_keypairs()
    signature = private_key.sign(test_message)
    public_key.verify(signature, test_message)


def validate_ssh_keypair(private_key_value: str, public_key_value: str) -> tuple[bool, str | None]:
    """
    Validate RSA keypair for SSH/SFTP connection.
    Args:
        private_key_value: PEM-encoded private key string (OpenSSL format)
        public_key_value: OpenSSH-encoded public key string
    Returns:
        tuple[bool, Optional[str]]:
            Tuple containing a boolean indicating if the keypair is valid,
            and an optional error message if invalid.
    """

    try:
        # Load the private key (PEM format)
        private_key = crypto_serialization.load_pem_private_key(
            private_key_value.encode(),
            password=None,  # No encryption as specified
        )
    except ValueError:
        return False, "Invalid private key format"

    try:
        # Load the public key (OpenSSH format)
        public_key = crypto_serialization.load_ssh_public_key(public_key_value.encode())
    except ValueError:
        return False, "Invalid public key format"

    try:
        match private_key, public_key:
            case rsa.RSAPrivateKey(), rsa.RSAPublicKey():
                _check_rsa_keypair(private_key, public_key)
            case ec.EllipticCurvePrivateKey(), ec.EllipticCurvePublicKey():
                _check_ecdsa_keypair(private_key, public_key)
            case ed25519.Ed25519PrivateKey(), ed25519.Ed25519PublicKey():
                _check_ed25519_keypair(private_key, public_key)
            case _:
                return (
                    False,
                    f"Unsupported pair of keys: private={type(private_key)}, public={type(public_key)}",
                )
    except InvalidSignature as e:
        return False, f"Keypair does not match: {e}"

    return True, None


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
