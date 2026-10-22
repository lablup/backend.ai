from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import (
    _AuthContext,
    _resolve_effective_context,
    _setup_user_context,
)
from ai.backend.manager.data.auth.types import AuthenticatedKeypair, AuthenticatedUser
from ai.backend.manager.errors.auth import (
    InsufficientPrivilege,
    InvalidAuthParameters,
    UserNotFound,
)

ACT_AS_HEADER = "X-BackendAI-Act-As"


def _make_request(*, headers: dict[str, str] | None = None) -> Any:
    return make_mocked_request("GET", "/v2/foo", headers=headers or {})


def _make_context(role: UserRole, *, user_id: uuid.UUID | None = None) -> _AuthContext:
    """An ``_AuthContext`` as the auth middleware reads it from the DB."""
    return _AuthContext(
        user=AuthenticatedUser(
            uuid=UserID(user_id or uuid.uuid4()),
            email=f"{role.value}@example.com",
            role=role,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
            sudo_session_enabled=False,
            allowed_client_ip=None,
            rate_limit=1000,
            resource_policy=MagicMock(),
        ),
        keypair=AuthenticatedKeypair(
            access_key=AccessKey(f"AK-{uuid.uuid4().hex[:8]}"),
            secret_key=SecretKey("secret"),
            is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
            resource_policy=MagicMock(),
        ),
    )


def _install_target_loader(
    monkeypatch: pytest.MonkeyPatch, target_id: uuid.UUID, target: _AuthContext | None
) -> None:
    async def _fake_load(db: Any, key_provider_pool: Any, user_id: UserID) -> _AuthContext | None:
        assert user_id == target_id
        return target

    monkeypatch.setattr(auth_mw, "_query_auth_context_by_user_id", _fake_load)


@dataclass(frozen=True)
class RejectCase:
    role: UserRole
    raw_target: str
    expected: type[Exception]


class TestResolveEffectiveContext:
    async def test_no_header_returns_authenticated_context(self) -> None:
        request = _make_request()
        caller = _make_context(UserRole.USER)
        effective = await _resolve_effective_context(request, MagicMock(), MagicMock(), caller)
        assert effective is caller

    async def test_superadmin_impersonates_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        target_id = uuid.uuid4()
        target = _make_context(UserRole.USER, user_id=target_id)
        _install_target_loader(monkeypatch, target_id, target)

        request = _make_request(headers={ACT_AS_HEADER: str(target_id)})
        caller = _make_context(UserRole.SUPERADMIN)
        effective = await _resolve_effective_context(request, MagicMock(), MagicMock(), caller)

        assert effective is target

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                RejectCase(UserRole.USER, str(uuid.uuid4()), InsufficientPrivilege),
                id="regular-user",
            ),
            pytest.param(
                RejectCase(UserRole.ADMIN, str(uuid.uuid4()), InsufficientPrivilege),
                id="domain-admin",
            ),
            pytest.param(
                RejectCase(UserRole.SUPERADMIN, "not-a-uuid", InvalidAuthParameters),
                id="invalid-uuid",
            ),
        ],
    )
    async def test_rejects(self, case: RejectCase) -> None:
        request = _make_request(headers={ACT_AS_HEADER: case.raw_target})
        caller = _make_context(case.role)
        with pytest.raises(case.expected):
            await _resolve_effective_context(request, MagicMock(), MagicMock(), caller)

    async def test_rejects_target_without_default_keypair(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target_id = uuid.uuid4()
        _install_target_loader(monkeypatch, target_id, None)

        request = _make_request(headers={ACT_AS_HEADER: str(target_id)})
        caller = _make_context(UserRole.SUPERADMIN)
        with pytest.raises(UserNotFound):
            await _resolve_effective_context(request, MagicMock(), MagicMock(), caller)


class TestSetupUserContext:
    def test_pushes_effective_as_current_and_trigger_as_triggered(self) -> None:
        effective = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="target-domain",
            domain_id=DomainID(uuid.uuid4()),
        )
        trigger = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name="default",
            domain_id=DomainID(uuid.uuid4()),
        )
        with _setup_user_context(effective, trigger):
            assert current_user() == effective
            assert triggered_user() == trigger
        assert current_user() is None
        assert triggered_user() is None

    def test_none_identities_push_nothing(self) -> None:
        with _setup_user_context(None, None):
            assert current_user() is None
            assert triggered_user() is None
