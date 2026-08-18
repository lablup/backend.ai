import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.types import FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey, SecretKey


@dataclass
class KeyPairCreator:
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int


@dataclass
class KeyPairSecrets:
    """Raw generated cryptographic material used before DB insert."""

    access_key: AccessKey
    secret_key: SecretKey
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class KeyPairData(FieldData):
    user_id: uuid.UUID
    access_key: AccessKey
    secret_key: SecretKey

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

    @override
    def owner_entity_id(self) -> UserID:
        return UserID(self.user_id)


@dataclass
class GeneratedKeyPairData:
    """Result of keypair creation. Contains the full keypair data including secrets."""

    keypair: KeyPairData
