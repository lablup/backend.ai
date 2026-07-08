from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import (
    _authenticated_user,
    _resolve_effective_user,
    _setup_user_context,
)
from ai.backend.manager.errors.auth import (
    InsufficientPrivilege,
    InvalidAuthParameters,
    UserNotFound,
)

ACT_AS_HEADER = "X-BackendAI-Act-As"


def _make_request(*, role: UserRole | None, headers: dict[str, str] | None = None) -> Any:
    request = make_mocked_request("GET", "/v2/foo", headers=headers or {})
    if role is not None:
        request["is_authorized"] = True
        request["is_admin"] = role in (UserRole.ADMIN, UserRole.SUPERADMIN)
        request["is_superadmin"] = role == UserRole.SUPERADMIN
        request["user"] = {
            "uuid": uuid.uuid4(),
            "role": role.value,
            "domain_name": "default",
        }
    return request


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
        request = _make_request(role=UserRole.USER)
        caller = _authenticated_user(request)
        assert caller is not None
        effective = await _resolve_effective_user(request, None, caller)  # type: ignore[arg-type]
        assert effective is caller

    async def test_superadmin_impersonates_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        target_id = uuid.uuid4()
        _install_target_loader(monkeypatch, target_id)

        request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(target_id)})
        caller = _authenticated_user(request)
        assert caller is not None
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

            async def _fake_load(db: Any, user_id: uuid.UUID) -> UserData:
                raise case.loader_error("Impersonation target user not found")

            monkeypatch.setattr(auth_mw, "_load_user_data", _fake_load)

        request = _make_request(role=case.role, headers={ACT_AS_HEADER: case.raw_target})
        caller = _authenticated_user(request)
        assert caller is not None
        with pytest.raises(case.expected):
            await _resolve_effective_user(request, None, caller)  # type: ignore[arg-type]


class TestSetupUserContext:
    async def test_no_header_current_equals_triggered(self) -> None:
        request = _make_request(role=UserRole.USER)
        caller_id = request["user"]["uuid"]
        with await _setup_user_context(request, None):  # type: ignore[arg-type]
            effective = current_user()
            trigger = triggered_user()
            assert effective is not None and trigger is not None
            assert effective == trigger
            assert effective.user_id == caller_id
        assert current_user() is None
        assert triggered_user() is None

    async def test_impersonation_current_is_target_triggered_is_caller(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target_id = uuid.uuid4()
        _install_target_loader(monkeypatch, target_id)

        request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(target_id)})
        caller_id = request["user"]["uuid"]
        with await _setup_user_context(request, None):  # type: ignore[arg-type]
            effective = current_user()
            trigger = triggered_user()
            assert effective is not None and trigger is not None
            assert effective.user_id == target_id
            assert trigger.user_id == caller_id
            assert trigger.is_superadmin
        assert current_user() is None
        assert triggered_user() is None
