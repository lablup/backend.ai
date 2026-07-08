from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.contexts.user import is_impersonating
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import (
    _resolve_identity,
    _setup_user_context,
    _user_data_from_auth_result,
)
from ai.backend.manager.errors.auth import (
    InsufficientPrivilege,
    InvalidAuthParameters,
    UserNotFound,
)

ACT_AS_HEADER = "X-BackendAI-Act-As"


def _make_request(*, role: UserRole | None, headers: dict[str, str] | None = None) -> Any:
    from aiohttp.test_utils import make_mocked_request

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


def _target_user(user_id: uuid.UUID) -> UserData:
    return UserData(
        user_id=user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="target-domain",
    )


async def test_no_header_effective_equals_trigger() -> None:
    request = _make_request(role=UserRole.USER)
    identity = await _resolve_identity(request, db=None)  # type: ignore[arg-type]
    assert identity.effective_user is not None
    assert identity.effective_user == identity.trigger_user
    assert identity.effective_user.user_id == request["user"]["uuid"]
    assert identity.impersonating is False


async def test_regular_user_with_header_is_rejected() -> None:
    request = _make_request(role=UserRole.USER, headers={ACT_AS_HEADER: str(uuid.uuid4())})
    with pytest.raises(InsufficientPrivilege):
        await _resolve_identity(request, db=None)  # type: ignore[arg-type]


async def test_superadmin_impersonates_target(monkeypatch: pytest.MonkeyPatch) -> None:
    target_id = uuid.uuid4()

    async def _fake_load(db: Any, user_id: uuid.UUID) -> UserData:
        assert user_id == target_id
        return _target_user(target_id)

    monkeypatch.setattr(auth_mw, "_load_user_data", _fake_load)

    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(target_id)})
    caller_id = request["user"]["uuid"]
    identity = await _resolve_identity(request, db=None)  # type: ignore[arg-type]

    assert identity.effective_user is not None and identity.trigger_user is not None
    assert identity.effective_user.user_id == target_id
    assert not identity.effective_user.is_superadmin
    assert identity.effective_user.domain_name == "target-domain"
    assert identity.trigger_user.user_id == caller_id
    assert identity.trigger_user.is_superadmin
    assert identity.impersonating is True


async def test_nonexistent_target_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_load(db: Any, user_id: uuid.UUID) -> UserData:
        raise UserNotFound("Impersonation target user not found")

    monkeypatch.setattr(auth_mw, "_load_user_data", _fake_load)

    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(uuid.uuid4())})
    with pytest.raises(UserNotFound):
        await _resolve_identity(request, db=None)  # type: ignore[arg-type]


async def test_invalid_uuid_header_is_rejected() -> None:
    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: "not-a-uuid"})
    with pytest.raises(InvalidAuthParameters):
        await _resolve_identity(request, db=None)  # type: ignore[arg-type]


def test_setup_user_context_sets_impersonation_flag_when_header_present() -> None:
    request = _make_request(role=UserRole.SUPERADMIN)
    caller = _user_data_from_auth_result(request)
    target = _target_user(uuid.uuid4())
    identity = auth_mw.RequestIdentity(target, caller, impersonating=True)
    assert not is_impersonating()
    with _setup_user_context(request, identity):
        assert is_impersonating()
    assert not is_impersonating()


def test_setup_user_context_no_flag_without_impersonation() -> None:
    request = _make_request(role=UserRole.USER)
    caller = _user_data_from_auth_result(request)
    identity = auth_mw.RequestIdentity(caller, caller)
    with _setup_user_context(request, identity):
        assert not is_impersonating()
