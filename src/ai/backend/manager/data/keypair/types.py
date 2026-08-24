import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.types import AccessKey
from ai.backend.manager.secret.types import SecretValue


@dataclass
class KeyPairCreator:
    is_active: bool
    is_admin: bool
    resource_policy: str
    # None leaves the column to its default rather than writing NULL.
    rate_limit: int | None = None


@dataclass
class KeyPairSecrets:
    """Generated cryptographic material used before DB insert. ``secret_key`` is
    already in its stored form, so it is bound as is."""

    access_key: AccessKey
    secret_key: SecretValue
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class KeyPairData(FieldData):
    id: KeyPairID
    user_id: uuid.UUID
    access_key: AccessKey
    # Stored form: plaintext for a legacy row, ciphertext once a write provider is named.
    # Decrypt through the key provider pool where the plaintext is needed.
    secret_key: SecretValue

    is_active: bool
    is_admin: bool
    is_default: bool
    created_at: datetime | None
    modified_at: datetime | None

    resource_policy_name: str
    rate_limit: int
    ssh_public_key: str | None
    ssh_private_key: str | None
    dotfiles: bytes
    bootstrap_script: str

    last_used: datetime | None = None
    num_queries: int = 0


@dataclass
class GeneratedKeyPairData:
    """Result of keypair creation. Contains the full keypair data including secrets."""

    keypair: KeyPairData
