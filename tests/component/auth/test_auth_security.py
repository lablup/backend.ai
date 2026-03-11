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
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import AuthenticationError, InvalidRequestError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetSSHKeypairResponse,
    SSHKeypairResponse,
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


@dataclass
class _KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class _CrossDomainUserData:
    user_uuid: uuid.UUID
    keypair: _KeypairFixtureData
    email: str


# ---------------------------------------------------------------------------
# Fixtures for password expiry tests (requires max_password_age config)
# ---------------------------------------------------------------------------


@dataclass
class ExpiredPasswordUserData:
    """User fixture with an expired password for testing password expiry flows."""

    user_uuid: uuid.UUID
    access_key: str
    secret_key: str
    password: str
    email: str
    domain_name: str


@pytest.fixture()
async def expired_password_user(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[ExpiredPasswordUserData]:
    """Insert a user whose password_changed_at is far in the past."""
    unique_id = secrets.token_hex(4)
    email = f"expired-pw-{unique_id}@test.local"
    password = f"ExpiredP@ss{unique_id}"
    data = ExpiredPasswordUserData(
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


# ---------------------------------------------------------------------------
# Fixtures for cross-domain tests
# ---------------------------------------------------------------------------


@dataclass
class CrossDomainFixtureData:
    """Holds a second domain with its own admin and user for cross-domain tests."""

    domain_name: str
    admin: _CrossDomainUserData
    user: _CrossDomainUserData
    group_id: uuid.UUID


@pytest.fixture()
async def cross_domain_fixture(
    db_engine: SAEngine,
    resource_policy_fixture: str,
) -> AsyncIterator[CrossDomainFixtureData]:
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
        # Create second domain
        await conn.execute(
            sa.insert(domains).values(
                name=domain_name,
                description=f"Cross-domain test {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
            )
        )
        # Create group in the second domain
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
        # Create domain-admin in second domain (ADMIN role, not SUPERADMIN)
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
        # Create regular user in second domain
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

    yield CrossDomainFixtureData(
        domain_name=domain_name,
        admin=admin_data,
        user=user_data,
        group_id=group_id,
    )

    async with db_engine.begin() as conn:
        # Cleanup in reverse order
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
    cross_domain_fixture: CrossDomainFixtureData,
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


# ============================================================================
# Test Classes
# ============================================================================


class TestPasswordChangeSelf:
    """Password change by the user themselves."""

    async def test_update_own_password_succeeds(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
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
        """After password change, authorize must succeed with the new password."""
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
        """After password change, authorize with old password must fail."""
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
    """Password expiry and max_password_age enforcement."""

    async def test_authorize_rejects_expired_password(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
    ) -> None:
        """When max_password_age is set and password is expired, authorize must fail."""
        # Temporarily set max_password_age on the config
        original_max_age = config_provider.config.auth.max_password_age
        try:
            config_provider.config.auth.max_password_age = timedelta(days=90)
            with pytest.raises(AuthenticationError):
                await admin_registry.auth.authorize(
                    AuthorizeRequest(
                        type=AuthTokenType.KEYPAIR,
                        domain=expired_password_user.domain_name,
                        username=expired_password_user.email,
                        password=expired_password_user.password,
                    ),
                )
        finally:
            config_provider.config.auth.max_password_age = original_max_age

    async def test_update_password_no_auth_with_expired_password(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
    ) -> None:
        """update_password_no_auth allows changing an expired password."""
        original_max_age = config_provider.config.auth.max_password_age
        try:
            config_provider.config.auth.max_password_age = timedelta(days=90)
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
        finally:
            config_provider.config.auth.max_password_age = original_max_age

    async def test_update_password_no_auth_rejected_when_not_configured(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
        config_provider: ManagerConfigProvider,
    ) -> None:
        """update_password_no_auth fails when max_password_age is not configured."""
        original_max_age = config_provider.config.auth.max_password_age
        try:
            config_provider.config.auth.max_password_age = None
            with pytest.raises(InvalidRequestError):
                await admin_registry.auth.update_password_no_auth(
                    UpdatePasswordNoAuthRequest(
                        domain=auth_user_fixture.domain_name,
                        username=auth_user_fixture.email,
                        current_password=auth_user_fixture.password,
                        new_password="AnyNewP@ss123",
                    ),
                )
        finally:
            config_provider.config.auth.max_password_age = original_max_age

    async def test_update_password_no_auth_same_password_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        expired_password_user: ExpiredPasswordUserData,
        config_provider: ManagerConfigProvider,
    ) -> None:
        """update_password_no_auth rejects setting the same password."""
        original_max_age = config_provider.config.auth.max_password_age
        try:
            config_provider.config.auth.max_password_age = timedelta(days=90)
            with pytest.raises(AuthenticationError):
                await admin_registry.auth.update_password_no_auth(
                    UpdatePasswordNoAuthRequest(
                        domain=expired_password_user.domain_name,
                        username=expired_password_user.email,
                        current_password=expired_password_user.password,
                        new_password=expired_password_user.password,
                    ),
                )
        finally:
            config_provider.config.auth.max_password_age = original_max_age


class TestSSHKeypairCRUD:
    """SSH keypair generate, list (get), and delete (overwrite) operations."""

    async def test_get_ssh_keypair_initially_empty(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.get_ssh_keypair()
        assert isinstance(result, GetSSHKeypairResponse)
        assert result.ssh_public_key == ""

    async def test_generate_ssh_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.generate_ssh_keypair()
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key != ""
        assert result.ssh_private_key != ""

    async def test_get_ssh_keypair_after_generate(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        generated = await user_registry.auth.generate_ssh_keypair()
        fetched = await user_registry.auth.get_ssh_keypair()
        assert fetched.ssh_public_key.strip() == generated.ssh_public_key.strip()

    async def test_upload_custom_ssh_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        privkey = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()
        pubkey = (
            private_key.public_key()
            .public_bytes(
                serialization.Encoding.OpenSSH,
                serialization.PublicFormat.OpenSSH,
            )
            .decode()
            .strip()
        )
        result = await user_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=pubkey, privkey=privkey),
        )
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key.strip() == pubkey
        assert result.ssh_private_key == privkey

    async def test_upload_overwrites_existing_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Uploading a new keypair overwrites the previously stored one."""
        # Generate first keypair
        await user_registry.auth.generate_ssh_keypair()

        # Upload a different custom keypair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        privkey = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()
        pubkey = (
            private_key.public_key()
            .public_bytes(
                serialization.Encoding.OpenSSH,
                serialization.PublicFormat.OpenSSH,
            )
            .decode()
            .strip()
        )
        await user_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=pubkey, privkey=privkey),
        )

        # Verify the stored key is the newly uploaded one
        fetched = await user_registry.auth.get_ssh_keypair()
        assert fetched.ssh_public_key.strip() == pubkey

    async def test_regenerate_replaces_previous_keypair(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Generating a new keypair replaces the previously stored one."""
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
        """Admin and regular user SSH keypairs are independent."""
        admin_kp = await admin_registry.auth.generate_ssh_keypair()
        user_kp = await user_registry.auth.generate_ssh_keypair()
        assert admin_kp.ssh_public_key != user_kp.ssh_public_key

        admin_fetched = await admin_registry.auth.get_ssh_keypair()
        user_fetched = await user_registry.auth.get_ssh_keypair()
        assert admin_fetched.ssh_public_key.strip() == admin_kp.ssh_public_key.strip()
        assert user_fetched.ssh_public_key.strip() == user_kp.ssh_public_key.strip()


class TestRoleAndScopeAccess:
    """Role-based scope access control tests."""

    async def test_superadmin_gets_superadmin_role(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "superadmin"
        assert result.domain_role == "admin"

    async def test_regular_user_gets_user_role(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "user"
        assert result.domain_role == "user"

    async def test_domain_admin_gets_admin_role(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await cross_domain_admin_registry.auth.get_role(GetRoleRequest())
        assert result.global_role == "user"
        assert result.domain_role == "admin"

    async def test_superadmin_can_verify_auth(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.verify_auth(
            VerifyAuthRequest(echo="superadmin-check"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"

    async def test_regular_user_can_verify_auth(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.verify_auth(
            VerifyAuthRequest(echo="user-check"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"

    async def test_domain_admin_can_verify_auth(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await cross_domain_admin_registry.auth.verify_auth(
            VerifyAuthRequest(echo="domain-admin-check"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"

    async def test_get_role_with_valid_group(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.auth.get_role(
            GetRoleRequest(group=group_fixture),
        )
        assert result.group_role is not None

    async def test_get_role_with_nonexistent_group_fails(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        fake_group = uuid.uuid4()
        with pytest.raises(Exception):
            await admin_registry.auth.get_role(
                GetRoleRequest(group=fake_group),
            )


class TestCrossDomainAccess:
    """Cross-domain access control: non-superadmin cannot access other domains."""

    async def test_superadmin_can_authorize_cross_domain_user(
        self,
        admin_registry: BackendAIClientRegistry,
        cross_domain_fixture: CrossDomainFixtureData,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """Superadmin can authorize a user from any domain."""
        result = await admin_registry.auth.authorize(
            AuthorizeRequest(
                type=AuthTokenType.KEYPAIR,
                domain=auth_user_fixture.domain_name,
                username=auth_user_fixture.email,
                password=auth_user_fixture.password,
            ),
        )
        assert isinstance(result, AuthorizeResponse)
        assert result.data.role == "user"

    async def test_domain_admin_role_is_scoped_to_own_domain(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
        cross_domain_fixture: CrossDomainFixtureData,
    ) -> None:
        """Domain admin role is correctly reported for their own domain."""
        result = await cross_domain_admin_registry.auth.get_role(GetRoleRequest())
        assert result.domain_role == "admin"
        assert result.global_role == "user"

    async def test_domain_admin_cannot_get_role_for_other_domain_group(
        self,
        cross_domain_admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """Domain admin cannot query group role for a group in another domain."""
        with pytest.raises(Exception):
            await cross_domain_admin_registry.auth.get_role(
                GetRoleRequest(group=group_fixture),
            )
