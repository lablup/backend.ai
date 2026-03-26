from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import sqlalchemy as sa
import yarl
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import AuthenticationError, InvalidRequestError, NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetSSHKeypairResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
    VerifyAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import GroupRow, association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import UserRole, users

from .conftest import AuthUserFixtureData

# ---------------------------------------------------------------------------
# Helper types
# ---------------------------------------------------------------------------


@dataclass
class _KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class _CrossDomainUserData:
    user_uuid: uuid.UUID
    keypair: _KeypairFixtureData
    email: str


@dataclass
class _ExpiredPasswordUserData:
    """User fixture with an expired password for testing password expiry flows."""

    user_uuid: uuid.UUID
    access_key: str
    secret_key: str
    password: str
    email: str
    domain_name: str


@dataclass
class _CrossDomainFixtureData:
    """Holds a second domain with its own admin and user for cross-domain tests."""

    domain_name: str
    admin: _CrossDomainUserData
    user: _CrossDomainUserData
    group_id: uuid.UUID


@dataclass
class _RSAKeypairData:
    public_key: str
    private_key: str


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def expired_password_user(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[_ExpiredPasswordUserData]:
    """Insert a user whose password_changed_at is far in the past."""
    unique_id = secrets.token_hex(4)
    email = f"expired-pw-{unique_id}@test.local"
    password = f"ExpiredP@ss{unique_id}"
    data = _ExpiredPasswordUserData(
        user_uuid=uuid.uuid4(),
        access_key=f"AKTEST{secrets.token_hex(7).upper()}",
        secret_key=secrets.token_hex(20),
        password=password,
        email=email,
        domain_name=domain_fixture,
    )
    # Set password_changed_at to 200 days ago so it's expired with a 90-day policy
    expired_at = datetime.now(UTC) - timedelta(days=200)
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"expired-pw-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=password,
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Expired PW User {unique_id}",
                description=f"Test expired password user {unique_id}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
                password_changed_at=expired_at,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.access_key,
                secret_key=data.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_fixture),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(keypairs.delete().where(keypairs.c.access_key == data.access_key))
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def cross_domain_fixture(
    db_engine: SAEngine,
    resource_policy_fixture: str,
) -> AsyncIterator[_CrossDomainFixtureData]:
    """Create a second domain with its own domain-admin and regular user."""
    domain_name = f"other-domain-{secrets.token_hex(6)}"
    group_id = uuid.uuid4()
    group_name = f"other-group-{secrets.token_hex(6)}"

    admin_unique = secrets.token_hex(4)
    admin_email = f"other-admin-{admin_unique}@test.local"
    admin_data = _CrossDomainUserData(
        user_uuid=uuid.uuid4(),
        keypair=_KeypairFixtureData(
            access_key=f"AKTEST{secrets.token_hex(7).upper()}",
            secret_key=secrets.token_hex(20),
        ),
        email=admin_email,
    )

    user_unique = secrets.token_hex(4)
    user_email = f"other-user-{user_unique}@test.local"
    user_data = _CrossDomainUserData(
        user_uuid=uuid.uuid4(),
        keypair=_KeypairFixtureData(
            access_key=f"AKTEST{secrets.token_hex(7).upper()}",
            secret_key=secrets.token_hex(20),
        ),
        email=user_email,
    )

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(domains).values(
                name=domain_name,
                description=f"Cross-domain test {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Cross-domain test group {group_name}",
                is_active=True,
                domain_name=domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        await conn.execute(
            sa.insert(users).values(
                uuid=str(admin_data.user_uuid),
                username=f"other-admin-{admin_unique}",
                email=admin_email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Other Domain Admin {admin_unique}",
                description=f"Cross-domain test admin {admin_unique}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_name,
                resource_policy=resource_policy_fixture,
                role=UserRole.ADMIN,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=admin_email,
                access_key=admin_data.keypair.access_key,
                secret_key=admin_data.keypair.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=True,
                user=str(admin_data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_id),
                user_id=str(admin_data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(users).values(
                uuid=str(user_data.user_uuid),
                username=f"other-user-{user_unique}",
                email=user_email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Other Domain User {user_unique}",
                description=f"Cross-domain test user {user_unique}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_name,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=user_email,
                access_key=user_data.keypair.access_key,
                secret_key=user_data.keypair.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(user_data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_id),
                user_id=str(user_data.user_uuid),
            )
        )

    yield _CrossDomainFixtureData(
        domain_name=domain_name,
        admin=admin_data,
        user=user_data,
        group_id=group_id,
    )

    async with db_engine.begin() as conn:
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id.in_([
                    str(admin_data.user_uuid),
                    str(user_data.user_uuid),
                ])
            )
        )
        await conn.execute(
            keypairs.delete().where(
                keypairs.c.access_key.in_([
                    admin_data.keypair.access_key,
                    user_data.keypair.access_key,
                ])
            )
        )
        await conn.execute(
            users.delete().where(
                users.c.uuid.in_([str(admin_data.user_uuid), str(user_data.user_uuid)])
            )
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))
        await conn.execute(domains.delete().where(domains.c.name == domain_name))


@pytest.fixture()
async def cross_domain_admin_registry(
    server: Any,
    cross_domain_fixture: _CrossDomainFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Registry authenticated as the admin of the second (cross) domain."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=cross_domain_fixture.admin.keypair.access_key,
            secret_key=cross_domain_fixture.admin.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
def rsa_keypair() -> _RSAKeypairData:
    """Generate an RSA keypair for testing SSH keypair upload."""
    private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    public_key_openssh = (
        private_key.public_key()
        .public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH,
        )
        .decode()
        .strip()
    )
    return _RSAKeypairData(public_key=public_key_openssh, private_key=private_key_pem)


# ============================================================================
# Test Classes
# ============================================================================


class TestVerifyAuth:
    """Verify HMAC-signed authentication for each role.

    Scenario: Confirm that verify_auth returns the correct response for each role,
    including the echo field round-trip and the authorized status.
    """

    async def test_admin_verifies_auth(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """A superadmin calling verify_auth must receive authorized='yes'
        and the echo field must be round-tripped back."""
        result = await admin_registry.auth.verify_auth(
            VerifyAuthRequest(echo="hello-from-admin"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "hello-from-admin"

    async def test_regular_user_verifies_auth(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """A regular user calling verify_auth must receive authorized='yes'
        and the echo field must be round-tripped back."""
        result = await user_registry.auth.verify_auth(
            VerifyAuthRequest(echo="hello-from-user"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "hello-from-user"

    async def test_domain_admin_verifies_auth(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
    ) -> None:
        """A domain-admin calling verify_auth must receive authorized='yes'.
        This confirms authentication itself is valid for a cross-domain admin's keypair."""
        result = await cross_domain_admin_registry.auth.verify_auth(
            VerifyAuthRequest(echo="domain-admin-check"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "domain-admin-check"


class TestRoleAndScopeAccess:
    """Role-based scope access control tests.

    Scenario: Verify that role-based access control works correctly.
    - Superadmin, regular user, and domain-admin each receive the correct global_role/domain_role
    - Querying a role for a specific group works correctly
    - Querying a role with a nonexistent group UUID raises an error
    """

    async def test_superadmin_gets_superadmin_role(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """A superadmin user's get_role response must return global_role='superadmin'
        and domain_role='admin'."""
        result = await admin_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "superadmin"
        assert result.domain_role == "admin"

    async def test_regular_user_gets_user_role(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """A regular user's get_role response must return both global_role
        and domain_role as 'user'."""
        result = await user_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "user"
        assert result.domain_role == "user"

    async def test_domain_admin_gets_admin_role(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
    ) -> None:
        """A domain-admin (ADMIN role, not SUPERADMIN) must receive global_role='user'
        and domain_role='admin' from get_role.
        This validates the privilege distinction between superadmin and domain-admin."""
        result = await cross_domain_admin_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "user"
        assert result.domain_role == "admin"

    async def test_get_role_with_valid_group(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """When get_role is called with a valid group UUID, the group_role field
        must be returned as a non-None value.
        This verifies that group-level role queries work correctly."""
        result = await admin_registry.auth.get_role(
            GetRoleRequest(group=group_fixture),
        )
        assert result.group_role is not None

    async def test_superadmin_get_role_with_nonexistent_group_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Superadmin calling get_role with a nonexistent group UUID must succeed
        because superadmins have global access across all domains and groups."""
        fake_group = uuid.uuid4()
        result = await admin_registry.auth.get_role(
            GetRoleRequest(group=fake_group),
        )
        assert result.group_role is not None

    async def test_regular_user_get_role_with_nonexistent_group_fails(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """A regular user calling get_role with a nonexistent group UUID must raise
        NotFoundError (404). Since no group membership exists in the database,
        the server responds with ObjectNotFound."""
        fake_group = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await user_registry.auth.get_role(
                GetRoleRequest(group=fake_group),
            )


class TestAuthorize:
    """Authorize (login) endpoint tests.

    Scenario: Verify the authorize endpoint issues credentials correctly
    and rejects invalid passwords.
    """

    async def test_authorize_returns_keypair_credentials(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """Authorizing with correct credentials must return non-empty access_key,
        secret_key, and the correct user role."""
        result = await admin_registry.auth.authorize(
            AuthorizeRequest(
                type=AuthTokenType.KEYPAIR,
                domain=auth_user_fixture.domain_name,
                username=auth_user_fixture.email,
                password=auth_user_fixture.password,
            ),
        )
        assert isinstance(result, AuthorizeResponse)
        assert result.data.access_key != ""
        assert result.data.secret_key != ""
        assert result.data.role == "user"

    async def test_authorize_with_wrong_password(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """Authorizing with an incorrect password must raise AuthenticationError (401)."""
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=auth_user_fixture.domain_name,
                    username=auth_user_fixture.email,
                    password="completely-wrong-password",
                ),
            )


class TestUpdateFullName:
    """Full name update tests."""

    async def test_admin_updates_full_name(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """An admin calling update_full_name must succeed."""
        result = await admin_registry.auth.update_full_name(
            UpdateFullNameRequest(
                email="ignored@test.local",
                full_name="Updated Admin Name",
            ),
        )
        assert isinstance(result, UpdateFullNameResponse)


class TestPasswordChange:
    """Password change by the user themselves.

    Scenario: Verify the self-initiated password change flow for regular users.
    - Succeeds when the correct old password and matching new password pair are provided
    - Fails with AuthenticationError when the old password is wrong
    - Fails with InvalidRequestError when new password and confirmation do not match
    - After a successful change, login with the new password succeeds
    - After a successful change, login with the old password is rejected
    """

    async def test_update_own_password_succeeds(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """When the user provides the correct old password and a matching new password pair,
        the password change should complete successfully."""
        new_password = f"NewP@ss{secrets.token_hex(4)}"
        result = await auth_user_registry.auth.update_password(
            UpdatePasswordRequest(
                old_password=auth_user_fixture.password,
                new_password=new_password,
                new_password2=new_password,
            ),
        )
        assert isinstance(result, UpdatePasswordResponse)
        assert result.error_msg is None

    async def test_update_password_wrong_old_password_fails(
        self,
        auth_user_registry: BackendAIClientRegistry,
    ) -> None:
        """When the old password is incorrect, AuthenticationError (401) must be raised.
        This validates the identity verification step during password change."""
        with pytest.raises(AuthenticationError):
            await auth_user_registry.auth.update_password(
                UpdatePasswordRequest(
                    old_password="completely-wrong-old-password",
                    new_password="NewP@ssw0rd!",
                    new_password2="NewP@ssw0rd!",
                ),
            )

    async def test_update_password_confirmation_mismatch(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """When new_password and new_password2 (confirmation) do not match,
        InvalidRequestError (400) must be raised.
        This prevents accidental password changes caused by typos."""
        with pytest.raises(InvalidRequestError):
            await auth_user_registry.auth.update_password(
                UpdatePasswordRequest(
                    old_password=auth_user_fixture.password,
                    new_password="NewP@ssw0rd!",
                    new_password2="MismatchP@ss!",
                ),
            )

    async def test_update_password_then_login_with_new_password(
        self,
        auth_user_registry: BackendAIClientRegistry,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """After a password change, authorize (login) with the new password must succeed.
        This is an end-to-end check that the change is actually persisted to the database."""
        new_password = f"Changed{secrets.token_hex(4)}!"
        await auth_user_registry.auth.update_password(
            UpdatePasswordRequest(
                old_password=auth_user_fixture.password,
                new_password=new_password,
                new_password2=new_password,
            ),
        )
        result = await admin_registry.auth.authorize(
            AuthorizeRequest(
                type=AuthTokenType.KEYPAIR,
                domain=auth_user_fixture.domain_name,
                username=auth_user_fixture.email,
                password=new_password,
            ),
        )
        assert isinstance(result, AuthorizeResponse)
        assert result.data.role == "user"

    async def test_old_password_rejected_after_change(
        self,
        auth_user_registry: BackendAIClientRegistry,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """After a password change, authorize with the old password must fail
        with AuthenticationError (401).
        This ensures the previous password is no longer valid."""
        old_password = auth_user_fixture.password
        new_password = f"Changed{secrets.token_hex(4)}!"
        await auth_user_registry.auth.update_password(
            UpdatePasswordRequest(
                old_password=old_password,
                new_password=new_password,
                new_password2=new_password,
            ),
        )
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=auth_user_fixture.domain_name,
                    username=auth_user_fixture.email,
                    password=old_password,
                ),
            )


class TestPasswordExpiry:
    """Password expiry and max_password_age enforcement.

    Scenario: Verify the password expiration policy (max_password_age) behavior.
    - When max_password_age is set and the password has expired, login is rejected
    - An expired password can be renewed via the no-auth password update endpoint
    - The no-auth password update is rejected when max_password_age is not configured
    - Renewing an expired password with the same password is rejected
    """

    async def test_authorize_rejects_expired_password(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: _ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With max_password_age=90 days, a user whose password_changed_at is 200 days ago
        must receive AuthenticationError (401) when attempting to authorize.
        This validates the security policy that blocks login for users with expired passwords."""
        monkeypatch.setattr(config_provider.config.auth, "max_password_age", timedelta(days=90))
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=expired_password_user.domain_name,
                    username=expired_password_user.email,
                    password=expired_password_user.password,
                ),
            )

    async def test_update_password_no_auth_with_expired_password(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: _ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A user with an expired password should be able to renew it via
        the update_password_no_auth API. This is the only path for users who cannot
        log in normally because their password has expired.
        The response must include a password_changed_at timestamp."""
        monkeypatch.setattr(config_provider.config.auth, "max_password_age", timedelta(days=90))
        new_password = f"RenewedP@ss{secrets.token_hex(4)}"
        result = await admin_registry.auth.update_password_no_auth(
            UpdatePasswordNoAuthRequest(
                domain=expired_password_user.domain_name,
                username=expired_password_user.email,
                current_password=expired_password_user.password,
                new_password=new_password,
            ),
        )
        assert isinstance(result, UpdatePasswordNoAuthResponse)
        assert result.password_changed_at != ""

    async def test_update_password_no_auth_rejected_when_not_configured(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
        config_provider: ManagerConfigProvider,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When max_password_age is not configured (None), calling update_password_no_auth
        must raise InvalidRequestError (400).
        There is no reason to use this API when the password expiry policy is disabled,
        so the request itself is rejected."""
        monkeypatch.setattr(config_provider.config.auth, "max_password_age", None)
        with pytest.raises(InvalidRequestError):
            await admin_registry.auth.update_password_no_auth(
                UpdatePasswordNoAuthRequest(
                    domain=auth_user_fixture.domain_name,
                    username=auth_user_fixture.email,
                    current_password=auth_user_fixture.password,
                    new_password="AnyNewP@ss123",
                ),
            )

    async def test_update_password_no_auth_same_password_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: _ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Attempting to renew an expired password with the same password must raise
        AuthenticationError (401).
        This prevents password reuse and ensures the expiry policy remains effective."""
        monkeypatch.setattr(config_provider.config.auth, "max_password_age", timedelta(days=90))
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.update_password_no_auth(
                UpdatePasswordNoAuthRequest(
                    domain=expired_password_user.domain_name,
                    username=expired_password_user.email,
                    current_password=expired_password_user.password,
                    new_password=expired_password_user.password,
                ),
            )


class TestSSHKeypair:
    """SSH keypair generate, get, and upload (overwrite) operations.

    Scenario: Verify the full CRUD lifecycle of SSH keypairs.
    - An empty public key is returned when no keypair has been generated yet
    - The server generates a valid SSH keypair with non-empty public and private keys
    - A generated keypair can be retrieved and matches the original
    - A user can upload a custom RSA keypair instead of using server-generated ones
    - Uploading a new keypair overwrites the previously stored one (one keypair per user)
    - Regenerating a keypair replaces the previous one
    - SSH keypairs are independent between different users
    """

    async def test_get_ssh_keypair_initially_empty(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """When a user who has never generated an SSH keypair calls get_ssh_keypair,
        an empty string should be returned. This verifies the correct initial state."""
        result = await user_registry.auth.get_ssh_keypair()
        assert isinstance(result, GetSSHKeypairResponse)
        assert result.ssh_public_key == ""

    async def test_generate_ssh_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Calling generate_ssh_keypair should make the server create an RSA keypair
        and return both public and private keys as non-empty strings."""
        result = await user_registry.auth.generate_ssh_keypair()
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key != ""
        assert result.ssh_private_key != ""

    async def test_get_ssh_keypair_after_generate(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """After generating a keypair, the public key returned by get_ssh_keypair
        must match the one returned at generation time.
        This confirms the generated key is correctly persisted in the database."""
        generated = await user_registry.auth.generate_ssh_keypair()
        fetched = await user_registry.auth.get_ssh_keypair()
        assert fetched.ssh_public_key.strip() == generated.ssh_public_key.strip()

    async def test_upload_custom_ssh_keypair(
        self,
        user_registry: BackendAIClientRegistry,
        rsa_keypair: _RSAKeypairData,
    ) -> None:
        """When a user uploads a locally generated RSA keypair via upload_ssh_keypair,
        the server should store it and return the same public/private key pair.
        This validates the scenario where users register their own keys
        instead of using server-generated ones."""
        result = await user_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=rsa_keypair.public_key, privkey=rsa_keypair.private_key),
        )
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key.strip() == rsa_keypair.public_key
        assert result.ssh_private_key == rsa_keypair.private_key

    async def test_upload_overwrites_existing_keypair(
        self,
        user_registry: BackendAIClientRegistry,
        rsa_keypair: _RSAKeypairData,
    ) -> None:
        """When a new custom keypair is uploaded while a server-generated keypair already exists,
        the existing keypair must be fully replaced by the new one.
        This validates the one-keypair-per-user policy."""
        await user_registry.auth.generate_ssh_keypair()

        await user_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=rsa_keypair.public_key, privkey=rsa_keypair.private_key),
        )

        fetched = await user_registry.auth.get_ssh_keypair()
        assert fetched.ssh_public_key.strip() == rsa_keypair.public_key

    async def test_regenerate_replaces_previous_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Calling generate_ssh_keypair twice should produce different keys,
        and the second one must replace the first.
        Fetching always returns the most recently generated keypair."""
        first = await user_registry.auth.generate_ssh_keypair()
        second = await user_registry.auth.generate_ssh_keypair()
        assert second.ssh_public_key != first.ssh_public_key

        fetched = await user_registry.auth.get_ssh_keypair()
        assert fetched.ssh_public_key.strip() == second.ssh_public_key.strip()

    async def test_each_user_has_independent_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """When admin and regular user each generate SSH keypairs, they should produce
        different keys, and each user's keypair must be stored/retrieved independently.
        This confirms SSH keypair isolation between users."""
        admin_kp = await admin_registry.auth.generate_ssh_keypair()
        user_kp = await user_registry.auth.generate_ssh_keypair()
        assert admin_kp.ssh_public_key != user_kp.ssh_public_key

        admin_fetched = await admin_registry.auth.get_ssh_keypair()
        user_fetched = await user_registry.auth.get_ssh_keypair()
        assert admin_fetched.ssh_public_key.strip() == admin_kp.ssh_public_key.strip()
        assert user_fetched.ssh_public_key.strip() == user_kp.ssh_public_key.strip()


class TestSignup:
    """User signup tests."""

    async def test_signup_creates_user_with_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
        db_engine: SAEngine,
    ) -> None:
        """Signing up a new user must return non-empty access_key and secret_key."""
        unique = secrets.token_hex(4)
        email = f"signup-{unique}@test.local"
        result = await admin_registry.auth.signup(
            SignupRequest(
                domain=domain_fixture,
                email=email,
                password=f"SignupP@ss{unique}",
                username=f"signup-{unique}",
                full_name=f"Signup User {unique}",
            ),
        )
        assert isinstance(result, SignupResponse)
        assert result.access_key != ""
        assert result.secret_key != ""

        # Cleanup: remove the signup-created user and keypair
        async with db_engine.begin() as conn:
            await conn.execute(keypairs.delete().where(keypairs.c.user_id == email))
            await conn.execute(users.delete().where(users.c.email == email))


class TestCrossDomainAccess:
    """Cross-domain access control: non-superadmin cannot access other domains.

    Scenario: Verify cross-domain access control enforcement.
    - A superadmin can query group roles for groups in another domain
    - A domain-admin's role is scoped to their own domain only
    - A domain-admin cannot query group roles for groups in another domain
    """

    async def test_superadmin_can_query_role_for_other_domain_group(
        self,
        admin_registry: BackendAIClientRegistry,
        cross_domain_fixture: _CrossDomainFixtureData,
    ) -> None:
        """A superadmin must be able to query group role for a group in another domain.
        This validates that superadmin's global privileges extend across domain boundaries,
        unlike domain-admins who are restricted to their own domain's groups."""
        result = await admin_registry.auth.get_role(
            GetRoleRequest(group=cross_domain_fixture.group_id),
        )
        assert result.group_role is not None

    async def test_domain_admin_role_is_scoped_to_own_domain(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
        cross_domain_fixture: _CrossDomainFixtureData,
    ) -> None:
        """A domain-admin's get_role must return domain_role='admin' for their own domain,
        but global_role='user'.
        This confirms domain-admin privileges are confined to their own domain."""
        result = await cross_domain_admin_registry.auth.get_role(GetRoleRequest())
        assert result.domain_role == "admin"
        assert result.global_role == "user"

    async def test_domain_admin_cannot_get_role_for_other_domain_group(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """A domain-admin attempting to query the group role for a group in another domain
        must receive NotFoundError (404).
        Access is denied because no membership exists for the user in that group."""
        with pytest.raises(NotFoundError):
            await cross_domain_admin_registry.auth.get_role(
                GetRoleRequest(group=group_fixture),
            )
