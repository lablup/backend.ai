from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.plugin.totp.webapp import deactivate_totp

_TARGET_EMAIL = "target@example.com"


def _requester(role: UserRole, domain_name: str) -> dict[str, object]:
    return {"email": "requester@example.com", "role": role, "domain_name": domain_name}


def _target(role: UserRole, domain_name: str) -> SimpleNamespace:
    return SimpleNamespace(
        totp_activated=True,
        totp_key="secret",
        role=role,
        domain_name=domain_name,
    )


@pytest.fixture
def update_conn() -> AsyncMock:
    return AsyncMock()


def _build_request(
    requester: dict[str, object],
    target: SimpleNamespace,
    update_conn: AsyncMock,
) -> web.Request:
    read_conn = AsyncMock()
    read_conn.execute.return_value = MagicMock(fetchone=MagicMock(return_value=target))
    db = MagicMock()
    db.begin_readonly.return_value.__aenter__.return_value = read_conn
    db.begin.return_value.__aenter__.return_value = update_conn
    app = web.Application()
    app["_root_app"] = {"_db": db}
    request = make_mocked_request("DELETE", f"/totp?email={_TARGET_EMAIL}", app=app)
    request["is_authorized"] = True
    request["is_admin"] = requester["role"] in (UserRole.ADMIN, UserRole.SUPERADMIN)
    request["is_superadmin"] = requester["role"] == UserRole.SUPERADMIN
    request["user"] = requester
    return request


class TestDeactivateTotpForAnotherUser:
    @pytest.mark.parametrize(
        ("requester", "target"),
        [
            (_requester(UserRole.ADMIN, "default"), _target(UserRole.USER, "default")),
            (_requester(UserRole.ADMIN, "default"), _target(UserRole.USER, "other")),
            (_requester(UserRole.ADMIN, "default"), _target(UserRole.SUPERADMIN, "default")),
            (_requester(UserRole.USER, "default"), _target(UserRole.USER, "default")),
        ],
        ids=[
            "domain-admin-same-domain-user",
            "domain-admin-other-domain-user",
            "domain-admin-same-domain-superadmin",
            "user-same-domain-user",
        ],
    )
    async def test_only_a_superadmin_may_deactivate_it(
        self,
        requester: dict[str, object],
        target: SimpleNamespace,
        update_conn: AsyncMock,
    ) -> None:
        request = _build_request(requester, target, update_conn)

        with pytest.raises(GenericForbidden):
            await deactivate_totp(request)

        update_conn.execute.assert_not_awaited()

    @pytest.mark.parametrize(
        "target",
        [_target(UserRole.USER, "other"), _target(UserRole.SUPERADMIN, "default")],
        ids=["other-domain-user", "superadmin"],
    )
    async def test_a_superadmin_deactivates_it(
        self,
        target: SimpleNamespace,
        update_conn: AsyncMock,
    ) -> None:
        request = _build_request(_requester(UserRole.SUPERADMIN, "default"), target, update_conn)

        response = await deactivate_totp(request)

        assert response.status == 200
        update_conn.execute.assert_awaited_once()
