from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserRole, UserStatus


@dataclass
class SSHKeypair:
    ssh_public_key: str
    ssh_private_key: str


@dataclass
class AuthorizationResult:
    user_id: uuid.UUID
    access_key: str
    secret_key: str
    role: str
    status: str


@dataclass
class UserData:
    uuid: uuid.UUID
    username: Optional[str]
    email: str
    password: Optional[str]
    need_password_change: bool
    full_name: Optional[str]
    description: Optional[str]
    is_active: bool
    status: UserStatus
    status_info: Optional[str]
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    password_changed_at: Optional[datetime]
    domain_name: str
    role: UserRole
    integration_id: Optional[str]
    resource_policy: str
    sudo_session_enabled: bool


@dataclass
class GroupMembershipData:
    group_id: uuid.UUID
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class KeyPairCredential:
    """KeyPair credential data for authentication."""

    user_id: str | None  # email
    access_key: str
    secret_key: str | None
    is_active: bool | None
    is_admin: bool | None
    created_at: datetime | None
    modified_at: datetime | None
    last_used: datetime | None
    rate_limit: int | None
    num_queries: int | None
    ssh_public_key: str | None
    ssh_private_key: str | None
    user: uuid.UUID  # user UUID
    resource_policy: str
    dotfiles: bytes
    bootstrap_script: str


@dataclass(frozen=True, slots=True)
class UserCredential:
    """User credential data for authentication (password, description, created_at excluded)."""

    uuid: uuid.UUID
    username: str | None
    email: str
    need_password_change: bool | None
    password_changed_at: datetime | None
    full_name: str | None
    status: UserStatus
    status_info: str | None
    modified_at: datetime | None
    integration_id: str | None
    domain_name: str | None
    role: UserRole | None
    allowed_client_ip: list[ReadableCIDR] | None
    totp_key: str | None
    totp_activated: bool | None
    resource_policy: str
    sudo_session_enabled: bool
    main_access_key: str | None


@dataclass(frozen=True, slots=True)
class CredentialsByAccessKey:
    """Credentials fetched by access key from database."""

    keypair: KeyPairCredential | None
    keypair_resource_policy: KeyPairResourcePolicyData | None
    user: UserCredential | None
    user_resource_policy: UserResourcePolicyData | None
