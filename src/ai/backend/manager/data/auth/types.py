import uuid
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Network, IPv6Network

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
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
    user_id: UserID
    access_key: AccessKey
    secret_key: SecretKey
    role: UserRole
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
    allowed_client_ip: list[ReadableCIDR[IPv4Network | IPv6Network]] | None
    resource_policy: UserResourcePolicyData


@dataclass(frozen=True)
class KeyPairSigningMaterial:
    """The owner and decrypted secret key of a keypair, as a signature check needs them."""

    user_id: UserID
    secret_key: str


@dataclass(frozen=True)
class AuthorizingUser:
    """The user record the authorize flow reads, and hands to its POST_AUTHORIZE plugins.

    Wider than what the flow itself checks: ``totp_activated``, ``totp_key`` and
    ``username`` are read by the two-factor plugins the flow dispatches to.
    """

    uuid: UserID
    username: str
    email: str
    status: UserStatus
    role: UserRole
    resource_policy: str
    password_changed_at: datetime | None
    totp_activated: bool
    totp_key: str | None


@dataclass(frozen=True)
class AuthenticatedKeypair:
    """The keypair the request authenticated with, limited to what request handling reads."""

    access_key: AccessKey
    secret_key: SecretKey
    is_admin: bool
    rate_limit: int | None
    resource_policy: KeyPairResourcePolicyData
