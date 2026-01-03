from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from dateutil.tz import gettz, tzutc

from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.api.auth import (
    _extract_auth_params,
    admin_required,
    auth_required,
    check_date,
    superadmin_required,
    validate_ip,
)
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    InvalidAuthParameters,
)
from ai.backend.manager.server import (
    agent_registry_ctx,
    database_ctx,
    event_dispatcher_plugin_ctx,
    event_hub_ctx,
    event_producer_ctx,
    hook_plugin_ctx,
    message_queue_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    redis_ctx,
    repositories_ctx,
    storage_manager_ctx,
)


def test_extract_auth_params():
    request = MagicMock(spec=web.Request)

    request.headers = {}
    assert _extract_auth_params(request) is None

    request.headers = {"Authorization": "no-space"}
    with pytest.raises(InvalidAuthParameters):
        _extract_auth_params(request)

    request.headers = {
        "Authorization": "BadAuthType signMethod=HMAC-SHA256,credential=fake-ak:fake-sig"
    }
    with pytest.raises(InvalidAuthParameters):
        _extract_auth_params(request)

    request.headers = {
        "Authorization": "BackendAI signMethod=HMAC-SHA256,credential=fake-ak:fake-sig"
    }
    ret = _extract_auth_params(request)
    assert ret is not None
    assert ret[0] == "HMAC-SHA256"
    assert ret[1] == "fake-ak"
    assert ret[2] == "fake-sig"


def test_check_date():
    # UserDict allows attribute assignment like types.SimpleNamespace
    # but also works like a plain dict.
    request = MagicMock(spec=web.Request)

    request.headers = {"X-Nothing": ""}
    assert not check_date(request)

    now = datetime.now(tzutc())
    request.headers = {"Date": now.isoformat()}
    assert check_date(request)

    # Timestamps without timezone info
    request.headers = {"Date": f"{now:%Y%m%dT%H:%M:%S}"}
    assert check_date(request)

    request.headers = {"Date": (now - timedelta(minutes=14, seconds=55)).isoformat()}
    assert check_date(request)
    request.headers = {"Date": (now + timedelta(minutes=14, seconds=55)).isoformat()}
    assert check_date(request)

    request.headers = {"Date": (now - timedelta(minutes=15, seconds=5)).isoformat()}
    assert not check_date(request)
    request.headers = {"Date": (now + timedelta(minutes=15, seconds=5)).isoformat()}
    assert not check_date(request)

    # RFC822-style date formatting used in plain HTTP
    request.headers = {"Date": "{:%a, %d %b %Y %H:%M:%S GMT}".format(now)}
    assert check_date(request)

    # RFC822-style date formatting used in plain HTTP with a non-UTC timezone
    now_kst = now.astimezone(gettz("Asia/Seoul"))
    request.headers = {"Date": "{:%a, %d %b %Y %H:%M:%S %Z}".format(now_kst)}
    assert check_date(request)
    now_est = now.astimezone(gettz("America/Panama"))
    request.headers = {"Date": "{:%a, %d %b %Y %H:%M:%S %Z}".format(now_est)}
    assert check_date(request)

    request.headers = {"Date": "some-unrecognizable-malformed-date-time"}
    assert not check_date(request)

    request.headers = {"X-BackendAI-Date": now.isoformat()}
    assert check_date(request)


@pytest.mark.asyncio
async def test_authorize(
    mock_etcd_ctx,
    mock_config_provider_ctx,
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    # The auth module requires config_server and database to be set up.
    app, client = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            redis_ctx,
            database_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            event_dispatcher_plugin_ctx,
            agent_registry_ctx,
        ],
        [".auth"],
    )

    async def do_authorize(hash_type, api_version):
        url = "/auth/test"
        req_data = {"echo": str(uuid.uuid4())}
        req_bytes = json.dumps(req_data).encode()
        headers = get_headers(
            "POST",
            url,
            req_bytes,
            hash_type=hash_type,
            api_version=api_version,
        )
        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == 200
        data = json.loads(await resp.text())
        assert data["authorized"] == "yes"
        assert data["echo"] == req_data["echo"]

    # Try multiple different hashing schemes
    await do_authorize("sha256", "v5.20191215")
    await do_authorize("sha256", "v4.20190615")
    await do_authorize("sha1", "v4.20190615")


# TODO: restore later. because migratation user schema and injection fixture keep failing.
# @pytest.mark.asyncio
# async def test_allowed_ip_authorize(
#     etcd_fixture, database_fixture, create_app_and_client, get_headers
# ):
#     app, client = await create_app_and_client(
#         [
#             shared_config_ctx,
#             redis_ctx,
#             event_dispatcher_ctx,
#             database_ctx,
#             monitoring_ctx,
#             hook_plugin_ctx,
#         ],
#         [".auth"],
#     )

#     allowed_client_ip = "10.10.10.10"
#     unallowed_client_ip = "10.10.20.20"

#     async def do_authorize():
#         url = "/auth/test"
#         req_data = {"echo": str(uuid.uuid4())}
#         req_bytes = json.dumps(req_data).encode()
#         headers = get_headers(
#             "POST",
#             url,
#             req_bytes,
#             allowed_ip=allowed_client_ip,
#         )
#         resp = await client.post(url, data=req_bytes, headers=headers)
#         assert resp.status == 200

#         headers = get_headers(
#             "POST",
#             url,
#             req_bytes,
#             allowed_ip=unallowed_client_ip,
#         )
#         resp = await client.post(url, data=req_bytes, headers=headers)
#         assert resp.status == 401

#     await do_authorize()


def test_validate_ip_allowed() -> None:
    """IP within CIDR range should be allowed, empty allowlist allows all."""
    request = MagicMock(spec=web.Request)
    request.headers = {"X-Forwarded-For": "10.0.0.50"}
    request.remote = None

    # Empty allowlist allows all IPs
    user: dict[str, Any] = {"allowed_client_ip": None}
    validate_ip(request, user)

    # IP within CIDR range is allowed
    user = {"allowed_client_ip": [ReadableCIDR("10.0.0.0/24", is_network=True)]}
    validate_ip(request, user)


def test_validate_ip_denied() -> None:
    """IP not in allowlist should raise AuthorizationFailed."""
    request = MagicMock(spec=web.Request)
    request.headers = {"X-Forwarded-For": "192.168.1.100"}
    request.remote = None

    user: dict[str, Any] = {"allowed_client_ip": [ReadableCIDR("10.0.0.0/24", is_network=True)]}
    with pytest.raises(AuthorizationFailed, match="not allowed IP address"):
        validate_ip(request, user)


class TestAuthDecorators:
    """Tests for auth_required, admin_required, superadmin_required decorators."""

    @pytest.mark.asyncio
    async def test_auth_required_authorized(self) -> None:
        """Authorized request should pass through."""

        @auth_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(side_effect=lambda k, d=None: {"is_authorized": True}.get(k, d))

        response = await handler(request)
        assert response.text == "ok"

    @pytest.mark.asyncio
    async def test_auth_required_unauthorized(self) -> None:
        """Unauthorized request should raise AuthorizationFailed."""

        @auth_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(side_effect=lambda k, d=None: {"is_authorized": False}.get(k, d))

        with pytest.raises(AuthorizationFailed, match="Unauthorized access"):
            await handler(request)

    @pytest.mark.asyncio
    async def test_auth_required_sets_handler_attr(self) -> None:
        """auth_required should set handler attributes."""

        @auth_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        # get_handler_attr expects request.match_info.handler, so we check _backend_attrs directly
        attrs = getattr(handler, "_backend_attrs", {})
        assert attrs.get("auth_required", False) is True
        assert attrs.get("auth_scope", None) == "user"

    @pytest.mark.asyncio
    async def test_admin_required_admin(self) -> None:
        """Admin request should pass through."""

        @admin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(
            side_effect=lambda k, d=None: {"is_authorized": True, "is_admin": True}.get(k, d)
        )

        response = await handler(request)
        assert response.text == "ok"

    @pytest.mark.asyncio
    async def test_admin_required_non_admin(self) -> None:
        """Non-admin request should raise AuthorizationFailed."""

        @admin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(
            side_effect=lambda k, d=None: {"is_authorized": True, "is_admin": False}.get(k, d)
        )

        with pytest.raises(AuthorizationFailed, match="Unauthorized access"):
            await handler(request)

    @pytest.mark.asyncio
    async def test_admin_required_unauthorized(self) -> None:
        """Unauthorized request should raise AuthorizationFailed."""

        @admin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(
            side_effect=lambda k, d=None: {"is_authorized": False, "is_admin": False}.get(k, d)
        )

        with pytest.raises(AuthorizationFailed, match="Unauthorized access"):
            await handler(request)

    @pytest.mark.asyncio
    async def test_admin_required_sets_handler_attr(self) -> None:
        """admin_required should set handler attributes."""

        @admin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        # get_handler_attr expects request.match_info.handler, so we check _backend_attrs directly
        attrs = getattr(handler, "_backend_attrs", {})
        assert attrs.get("auth_required", False) is True
        assert attrs.get("auth_scope", None) == "admin"

    @pytest.mark.asyncio
    async def test_superadmin_required_superadmin(self) -> None:
        """Superadmin request should pass through."""

        @superadmin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(
            side_effect=lambda k, d=None: {"is_authorized": True, "is_superadmin": True}.get(k, d)
        )

        response = await handler(request)
        assert response.text == "ok"

    @pytest.mark.asyncio
    async def test_superadmin_required_admin_only(self) -> None:
        """Admin (not superadmin) request should raise AuthorizationFailed."""

        @superadmin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        request = MagicMock(spec=web.Request)
        request.get = MagicMock(
            side_effect=lambda k, d=None: {
                "is_authorized": True,
                "is_admin": True,
                "is_superadmin": False,
            }.get(k, d)
        )

        with pytest.raises(AuthorizationFailed, match="Unauthorized access"):
            await handler(request)

    @pytest.mark.asyncio
    async def test_superadmin_required_sets_handler_attr(self) -> None:
        """superadmin_required should set handler attributes."""

        @superadmin_required
        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        # get_handler_attr expects request.match_info.handler, so we check _backend_attrs directly
        attrs = getattr(handler, "_backend_attrs", {})
        assert attrs.get("auth_required", False) is True
        assert attrs.get("auth_scope", None) == "superadmin"
