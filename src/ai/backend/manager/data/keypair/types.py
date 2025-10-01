import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.common.types import AccessKey, SecretKey


@dataclass
class KeyPairCreator:
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int


@dataclass
class GeneratedKeyPairData:
    access_key: AccessKey
    secret_key: SecretKey
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class KeyPairData:
    user_id: uuid.UUID
    access_key: AccessKey
    secret_key: SecretKey

    is_active: bool
    is_admin: bool
    created_at: Optional[datetime]
    modified_at: Optional[datetime]

    resource_policy_name: str
    rate_limit: int
    ssh_public_key: Optional[str]
    ssh_private_key: Optional[str]
    dotfiles: str
    bootstrap_script: str
