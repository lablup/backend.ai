"""Tests for max_concurrent_logins enforcement in AuthService._create_login_session."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.errors.auth import TooManyConcurrentLoginSessions
from ai.backend.manager.models.login_session.enums import LoginAttemptResult
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.db_source.db_source import (
    ActiveSessionInfo,
    LoginSessionCreationResult,
)
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.service import AuthService

_DEFAULT_USER_UUID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_DEFAULT_RESOURCE_POLICY = "default"


def _make_auth_config() -> AuthConfig:
    return AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
        login_session_max_age=604800,
    )


def _make_mock_user(resource_policy: str = _DEFAULT_RESOURCE_POLICY) -> MagicMock:
    """Create a minimal mock user RowMapping for _create_login_session."""
    mock_user = MagicMock()
    mock_user.uuid = _DEFAULT_USER_UUID
    mock_user.resource_policy = resource_policy
    mock_user.role = UserRole.USER
    mock_user.status = UserStatus.ACTIVE
    mock_user.__getitem__ = lambda self, key: getattr(self, key)
    return mock_user


def _make_mock_keypair_row() -> MagicMock:
    """Create a mock keypair row."""
    mock_keypair = MagicMock()
    mock_keypair.access_key = "AKIAIOSFODNN7EXAMPLE"
    mock_keypair.secret_key = "secret"
    return mock_keypair


def _make_action(*, force: bool = False) -> AuthorizeAction:
    return AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="user@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
        force=force,
    )


def _make_policy(max_concurrent_logins: int | None) -> UserResourcePolicyData:
    return UserResourcePolicyData(
        name=_DEFAULT_RESOURCE_POLICY,
        max_vfolder_count=10,
        max_quota_scope_size=0,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
        max_concurrent_logins=max_concurrent_logins,
    )


def _make_live_sessions(count: int) -> list[ActiveSessionInfo]:
    """Create a list of fake live session infos, oldest first."""
    base_time = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        ActiveSessionInfo(
            session_token=f"token_{i}",
            created_at=base_time + timedelta(minutes=i),
        )
        for i in range(count)
    ]


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    repo = AsyncMock(spec=AuthRepository)
    repo.create_login_session.return_value = LoginSessionCreationResult(
        session_token="test_session_token",
    )
    return repo


@pytest.fixture
def mock_user_resource_policy_repository() -> AsyncMock:
    return AsyncMock(spec=UserResourcePolicyRepository)


@pytest.fixture
def mock_valkey_session_client() -> AsyncMock:
    return AsyncMock(spec=ValkeySessionClient)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: MagicMock,
    mock_valkey_session_client: AsyncMock,
    mock_user_resource_policy_repository: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
        valkey_session_client=mock_valkey_session_client,
        user_resource_policy_repository=mock_user_resource_policy_repository,
    )


@dataclass(frozen=True)
class RejectCase:
    """A scenario where ``_create_login_session`` must raise ``TooManyConcurrentLoginSessions``.

    These cases describe a user who is at or over their per-user login-session cap and
    is NOT opting into the force-evict-oldest behavior, so the new login must be denied.
    """

    # The ``user_resource_policy.max_concurrent_logins`` value configured for the user.
    configured_max_logins: int
    # How many login sessions the user already has active (cross-checked against Valkey).
    existing_active_sessions: int
    # Whether the incoming AuthorizeAction has ``force=True`` (evict oldest) set.
    force_evict_oldest: bool


@dataclass(frozen=True)
class AllowCase:
    """A scenario where ``_create_login_session`` must proceed and create the new session.

    Covers both "below the cap" paths and the "force-evict-oldest" path. The expected
    eviction list captures exactly which existing session tokens the service should
    pass to ``AuthRepository.create_login_session`` as ``tokens_to_invalidate``.
    """

    # The ``user_resource_policy.max_concurrent_logins`` value. ``None`` means unlimited.
    # Ignored when ``policy_lookup_fails`` is True.
    configured_max_logins: int | None
    # How many login sessions the user already has active.
    existing_active_sessions: int
    # Whether the incoming AuthorizeAction has ``force=True`` (evict oldest) set.
    force_evict_oldest: bool
    # When True, simulate the user having no resolvable user_resource_policy
    # (repository raises ``UserResourcePolicyNotFound``). Enforcement should then be
    # skipped entirely (treated as unlimited).
    policy_lookup_fails: bool
    # Exact ``tokens_to_invalidate`` value expected in the repository call.
    # ``None`` means no eviction (below cap, unlimited, or policy missing).
    # A list means force-evict those exact oldest tokens in order.
    expected_evicted_tokens: list[str] | None


class TestMaxConcurrentLoginsEnforcement:
    """Tests for the max_concurrent_logins enforcement logic in _create_login_session.

    Enforcement is driven entirely by ``live_sessions`` (the already-cross-checked active
    set) and ``user_resource_policy.max_concurrent_logins``.  No extra DB count query is
    issued.
    """

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                RejectCase(
                    configured_max_logins=1,
                    existing_active_sessions=1,
                    force_evict_oldest=False,
                ),
                id="limit-1-1-live-no-force",
            ),
            pytest.param(
                RejectCase(
                    configured_max_logins=5,
                    existing_active_sessions=5,
                    force_evict_oldest=False,
                ),
                id="limit-5-5-live-no-force",
            ),
            # Non-positive caps must reject regardless of force (no number of evictions
            # can bring a fresh login back under a cap of 0).
            pytest.param(
                RejectCase(
                    configured_max_logins=0,
                    existing_active_sessions=0,
                    force_evict_oldest=True,
                ),
                id="limit-0-no-sessions-force-rejected",
            ),
            pytest.param(
                RejectCase(
                    configured_max_logins=0,
                    existing_active_sessions=3,
                    force_evict_oldest=True,
                ),
                id="limit-0-with-sessions-force-rejected",
            ),
        ],
    )
    async def test_rejects_when_limit_reached_without_force(
        self,
        auth_service: AuthService,
        mock_user_resource_policy_repository: AsyncMock,
        case: RejectCase,
    ) -> None:
        """At or over the limit without force → raises TooManyConcurrentLoginSessions."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=case.configured_max_logins
        )

        with pytest.raises(TooManyConcurrentLoginSessions):
            await auth_service._create_login_session(
                action=_make_action(force=case.force_evict_oldest),
                user=_make_mock_user(),
                keypair_row=_make_mock_keypair_row(),
                live_sessions=_make_live_sessions(case.existing_active_sessions),
                auth_config=_make_auth_config(),
            )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                AllowCase(
                    configured_max_logins=1,
                    existing_active_sessions=0,
                    force_evict_oldest=False,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=None,
                ),
                id="limit-1-0-live-succeeds",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=5,
                    existing_active_sessions=4,
                    force_evict_oldest=False,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=None,
                ),
                id="limit-5-4-live-succeeds",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=None,
                    existing_active_sessions=9999,
                    force_evict_oldest=False,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=None,
                ),
                id="unlimited-no-enforcement",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=5,
                    existing_active_sessions=5,
                    force_evict_oldest=False,
                    policy_lookup_fails=True,
                    expected_evicted_tokens=None,
                ),
                id="missing-policy-no-enforcement",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=5,
                    existing_active_sessions=3,
                    force_evict_oldest=True,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=None,
                ),
                id="force-below-limit-no-evict",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=1,
                    existing_active_sessions=2,
                    force_evict_oldest=True,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=["token_0", "token_1"],
                ),
                id="force-evict-oldest-2",
            ),
            pytest.param(
                AllowCase(
                    configured_max_logins=5,
                    existing_active_sessions=5,
                    force_evict_oldest=True,
                    policy_lookup_fails=False,
                    expected_evicted_tokens=["token_0"],
                ),
                id="force-evict-oldest-1",
            ),
        ],
    )
    async def test_allows_login_and_tokens_to_invalidate(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
        case: AllowCase,
    ) -> None:
        """Non-raising scenarios: verify login proceeds with the expected tokens_to_invalidate."""
        if case.policy_lookup_fails:
            mock_user_resource_policy_repository.get_by_name.side_effect = (
                UserResourcePolicyNotFound("Policy not found")
            )
        else:
            mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
                max_concurrent_logins=case.configured_max_logins
            )

        result = await auth_service._create_login_session(
            action=_make_action(force=case.force_evict_oldest),
            user=_make_mock_user(),
            keypair_row=_make_mock_keypair_row(),
            live_sessions=_make_live_sessions(case.existing_active_sessions),
            auth_config=_make_auth_config(),
        )

        delete_mock = mock_auth_repository.delete_login_sessions_by_tokens
        if case.expected_evicted_tokens is None:
            delete_mock.assert_not_called()
        else:
            delete_mock.assert_called_once_with(
                case.expected_evicted_tokens, LoginAttemptResult.EVICTED
            )
        assert result.authorization_result is not None
