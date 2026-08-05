from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.identifier.domain import DomainID
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import (
    _resolve_effective_user,
    _setup_user_context,
)
from ai.backend.manager.errors.auth import (
    InsufficientPrivilege,
    InvalidAuthParameters,
    UserNotFound,
)

ACT_AS_HEADER = "X-BackendAI-Act-As"


def _make_request(*, headers: dict[str, str] | None = None) -> Any:
    return make_mocked_request("GET", "/v2/foo", headers=headers or {})


def _make_caller(role: UserRole) -> UserData:
    """The caller's ``UserData`` as the auth middleware builds it."""
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


def _install_target_loader(monkeypatch: pytest.MonkeyPatch, target_id: uuid.UUID) -> None:
    async def _fake_load(db: Any, user_id: uuid.UUID) -> UserData:
        assert user_id == target_id
        return UserData(
            user_id=target_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="target-domain",
            domain_id=DomainID(uuid.uuid4()),
        )

    monkeypatch.setattr(auth_mw, "_load_user_data", _fake_load)


@dataclass(frozen=True)
class RejectCase:
    role: UserRole
    raw_target: str
    expected: type[Exception]
    # Fake loader raises this so the target-not-found path can be exercised; None skips it.
    loader_error: type[Exception] | None = None


class TestResolveEffectiveUser:
    async def test_no_header_returns_authenticated_user(self) -> None:
        request = _make_request()
        caller = _make_caller(UserRole.USER)
        effective = await _resolve_effective_user(request, None, caller)  # type: ignore[arg-type]
        assert effective is caller

    async def test_superadmin_impersonates_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        target_id = uuid.uuid4()
        _install_target_loader(monkeypatch, target_id)

        request = _make_request(headers={ACT_AS_HEADER: str(target_id)})
        caller = _make_caller(UserRole.SUPERADMIN)
        effective = await _resolve_effective_user(request, None, caller)  # type: ignore[arg-type]

        assert effective.user_id == target_id
        assert not effective.is_superadmin
        assert effective.domain_name == "target-domain"

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                RejectCase(UserRole.USER, str(uuid.uuid4()), InsufficientPrivilege),
                id="regular-user",
            ),
            pytest.param(
                RejectCase(UserRole.SUPERADMIN, "not-a-uuid", InvalidAuthParameters),
                id="invalid-uuid",
            ),
            pytest.param(
                RejectCase(
                    UserRole.SUPERADMIN, str(uuid.uuid4()), UserNotFound, loader_error=UserNotFound
                ),
                id="target-not-found",
            ),
        ],
    )
    async def test_rejects(self, monkeypatch: pytest.MonkeyPatch, case: RejectCase) -> None:
        if case.loader_error is not None:
            error_cls = case.loader_error

            async def _fake_load(db: Any, user_id: uuid.UUID) -> UserData:
                raise error_cls("Impersonation target user not found")

            monkeypatch.setattr(auth_mw, "_load_user_data", _fake_load)

        request = _make_request(headers={ACT_AS_HEADER: case.raw_target})
        caller = _make_caller(case.role)
        with pytest.raises(case.expected):
            await _resolve_effective_user(request, None, caller)  # type: ignore[arg-type]


class TestSetupUserContext:
    def test_pushes_effective_as_current_and_trigger_as_triggered(self) -> None:
        request = _make_request()
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
        with _setup_user_context(request, effective, trigger):
            assert current_user() == effective
            assert triggered_user() == trigger
        assert current_user() is None
        assert triggered_user() is None

    def test_none_identities_push_nothing(self) -> None:
        request = _make_request()
        with _setup_user_context(request, None, None):
            assert current_user() is None
            assert triggered_user() is None
