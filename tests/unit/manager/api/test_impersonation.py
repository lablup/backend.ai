from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import (
    ACT_AS_HEADER,
    _resolve_impersonation,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege, InvalidAuthParameters
from ai.backend.manager.errors.common import ObjectNotFound


def _make_request(
    *,
    role: UserRole | None,
    headers: dict[str, str] | None = None,
    query: str = "",
) -> Any:
    path = "/v2/foo"
    if query:
        path = f"{path}?{query}"
    request = make_mocked_request("GET", path, headers=headers or {})
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


@pytest.mark.asyncio
async def test_no_header_effective_equals_trigger() -> None:
    request = _make_request(role=UserRole.USER)
    effective, trigger = await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]
    assert effective is not None
    assert effective == trigger
    assert effective.user_id == request["user"]["uuid"]


@pytest.mark.asyncio
async def test_regular_user_with_header_is_rejected() -> None:
    target = uuid.uuid4()
    request = _make_request(role=UserRole.USER, headers={ACT_AS_HEADER: str(target)})
    with pytest.raises(InsufficientPrivilege):
        await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_superadmin_impersonates_target(monkeypatch: pytest.MonkeyPatch) -> None:
    target_id = uuid.uuid4()

    async def _fake_query(db: Any, tid: uuid.UUID) -> Any:
        assert tid == target_id
        return SimpleNamespace(uuid=target_id, role=UserRole.USER, domain_name="target-domain")

    monkeypatch.setattr(auth_mw, "_query_target_user", _fake_query)

    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(target_id)})
    caller_id = request["user"]["uuid"]
    effective, trigger = await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]

    assert effective is not None and trigger is not None
    assert effective.user_id == target_id
    assert effective.role == UserRole.USER
    assert not effective.is_superadmin
    assert effective.domain_name == "target-domain"
    assert trigger.user_id == caller_id
    assert trigger.is_superadmin


@pytest.mark.asyncio
async def test_nonexistent_target_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_query(db: Any, tid: uuid.UUID) -> Any:
        return None

    monkeypatch.setattr(auth_mw, "_query_target_user", _fake_query)

    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(uuid.uuid4())})
    with pytest.raises(ObjectNotFound):
        await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_invalid_uuid_header_is_rejected() -> None:
    request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: "not-a-uuid"})
    with pytest.raises(InvalidAuthParameters):
        await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_header_with_owner_access_key_query_is_rejected() -> None:
    request = _make_request(
        role=UserRole.SUPERADMIN,
        headers={ACT_AS_HEADER: str(uuid.uuid4())},
        query="owner_access_key=AKIATEST",
    )
    with pytest.raises(InvalidAuthParameters):
        await _resolve_impersonation(request, db=None)  # type: ignore[arg-type]
