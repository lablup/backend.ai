import uuid
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Network, IPv6Network

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import AccessKey, ReadableCIDR, SecretKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserStatus


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
    session_token: str


@dataclass
class UserData:
    uuid: uuid.UUID
    username: str
    email: str
    password: str | None
    need_password_change: bool
    full_name: str | None
    description: str | None
    is_active: bool
    status: UserStatus
    status_info: str | None
    created_at: datetime | None
    modified_at: datetime | None
    password_changed_at: datetime | None
    domain_name: str
    role: UserRole
    integration_name: str | None
    resource_policy: str
    sudo_session_enabled: bool


@dataclass
class GroupMembershipData:
    group_id: uuid.UUID
    user_id: uuid.UUID


@dataclass(frozen=True)
class UserCreationData:
    """A fully provisioned user and its default keypair."""

    user: UserData
    keypair: KeyPairData


@dataclass(frozen=True)
class AuthenticatedUser:
    """The authenticated caller's user record, limited to what request handling reads."""

    uuid: UserID
    email: str
    role: UserRole
    domain_name: str
    domain_id: DomainID
    sudo_session_enabled: bool
    main_access_key: AccessKey | None
    allowed_client_ip: list[ReadableCIDR[IPv4Network | IPv6Network]] | None
    resource_policy: UserResourcePolicyData


@dataclass(frozen=True)
class AuthenticatedKeypair:
    """The keypair the request authenticated with, limited to what request handling reads."""

    access_key: AccessKey
    secret_key: SecretKey | None
    is_admin: bool
    rate_limit: int | None
    resource_policy: KeyPairResourcePolicyData
