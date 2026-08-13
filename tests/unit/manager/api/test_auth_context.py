from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AccessKey,
    DefaultForUnspecified,
    ResourceSlot,
    SecretKey,
)
from ai.backend.manager.api.rest.middleware.auth import _apply_auth_context, _AuthContext
from ai.backend.manager.data.auth.types import AuthenticatedKeypair, AuthenticatedUser
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    UserResourcePolicyData,
)


@pytest.fixture
def base_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        uuid=UserID(uuid.uuid4()),
        email="caller@example.com",
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
        sudo_session_enabled=False,
        allowed_client_ip=None,
        resource_policy=UserResourcePolicyData(name="default"),
    )


@pytest.fixture
def base_keypair() -> AuthenticatedKeypair:
    return AuthenticatedKeypair(
        access_key=AccessKey("AKTESTCALLER"),
        secret_key=SecretKey("caller-secret"),
        is_admin=False,
        rate_limit=None,
        resource_policy=KeyPairResourcePolicyData(
            name="default",
            created_at=None,
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=ResourceSlot(),
            max_session_lifetime=0,
            max_concurrent_sessions=5,
            max_pending_session_count=None,
            max_pending_session_resource_slots=None,
            max_priority=None,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=600,
            allowed_vfolder_hosts={},
        ),
    )


@dataclass(frozen=True)
class _FlagCase:
    role: UserRole
    expected_is_admin: bool
    expected_is_superadmin: bool


class TestApplyAuthContext:
    @pytest.mark.parametrize(
        "case",
        [
            _FlagCase(UserRole.SUPERADMIN, expected_is_admin=True, expected_is_superadmin=True),
            _FlagCase(UserRole.ADMIN, expected_is_admin=True, expected_is_superadmin=False),
            _FlagCase(UserRole.USER, expected_is_admin=False, expected_is_superadmin=False),
            _FlagCase(UserRole.MONITOR, expected_is_admin=False, expected_is_superadmin=False),
        ],
        ids=lambda case: case.role.value,
    )
    def test_flags_derive_from_user_role(
        self,
        case: _FlagCase,
        base_user: AuthenticatedUser,
        base_keypair: AuthenticatedKeypair,
    ) -> None:
        request: Any = make_mocked_request("GET", "/v2/foo")
        # The keypair flag is set to the opposite of the expectation so the
        # assertions fail if it still feeds the request flags.
        context = _AuthContext(
            user=dataclasses.replace(base_user, role=case.role),
            keypair=dataclasses.replace(base_keypair, is_admin=not case.expected_is_admin),
        )

        authenticated_user = _apply_auth_context(request, context)

        assert request["is_authorized"] is True
        assert request["is_admin"] is case.expected_is_admin
        assert request["is_superadmin"] is case.expected_is_superadmin
        assert authenticated_user == UserData(
            user_id=context.user.uuid,
            is_authorized=True,
            is_admin=case.expected_is_admin,
            is_superadmin=case.expected_is_superadmin,
            role=case.role,
            domain_name=context.user.domain_name,
            domain_id=context.user.domain_id,
        )

    def test_keypair_map_excludes_secret_key(
        self,
        base_user: AuthenticatedUser,
        base_keypair: AuthenticatedKeypair,
    ) -> None:
        request: Any = make_mocked_request("GET", "/v2/foo")
        context = _AuthContext(user=base_user, keypair=base_keypair)

        _apply_auth_context(request, context)

        assert set(request["keypair"].keys()) == {
            "access_key",
            "is_admin",
            "rate_limit",
            "resource_policy",
        }
        assert request["keypair"]["access_key"] == context.keypair.access_key
        assert request["user"]["uuid"] == context.user.uuid
