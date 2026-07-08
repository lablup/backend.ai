from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.rest.middleware import auth as auth_mw
from ai.backend.manager.api.rest.middleware.auth import _resolve_requester_identity
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


@dataclass(frozen=True)
class RejectCase:
    role: UserRole
    raw_target: str
    expected: type[Exception]
    # Fake loader raises this so the target-not-found path can be exercised; None skips it.
    loader_error: type[Exception] | None = None


class TestResolveRequesterIdentity:
    async def test_no_header_effective_equals_trigger(self) -> None:
        request = _make_request(role=UserRole.USER)
        identity = await _resolve_requester_identity(request, db=None)  # type: ignore[arg-type]
        assert identity.effective_user is not None
        assert identity.effective_user == identity.trigger_user
        assert identity.effective_user.user_id == request["user"]["uuid"]

    async def test_superadmin_impersonates_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        target_id = uuid.uuid4()

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

        request = _make_request(role=UserRole.SUPERADMIN, headers={ACT_AS_HEADER: str(target_id)})
        caller_id = request["user"]["uuid"]
        identity = await _resolve_requester_identity(request, db=None)  # type: ignore[arg-type]

        assert identity.effective_user is not None and identity.trigger_user is not None
        assert identity.effective_user.user_id == target_id
        assert not identity.effective_user.is_superadmin
        assert identity.effective_user.domain_name == "target-domain"
        assert identity.trigger_user.user_id == caller_id
        assert identity.trigger_user.is_superadmin

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
        with pytest.raises(case.expected):
            await _resolve_requester_identity(request, db=None)  # type: ignore[arg-type]
