import json
import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from dateutil.tz import gettz, tzutc

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.middleware.auth import _extract_auth_params, check_date
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.errors.auth import InvalidAuthParameters


def test_extract_auth_params() -> None:
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


def test_check_date() -> None:
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
    request.headers = {"Date": f"{now:%a, %d %b %Y %H:%M:%S GMT}"}
    assert check_date(request)

    # RFC822-style date formatting used in plain HTTP with a non-UTC timezone
    now_kst = now.astimezone(gettz("Asia/Seoul"))
    request.headers = {"Date": f"{now_kst:%a, %d %b %Y %H:%M:%S %Z}"}
    assert check_date(request)
    now_est = now.astimezone(gettz("America/Panama"))
    request.headers = {"Date": f"{now_est:%a, %d %b %Y %H:%M:%S %Z}"}
    assert check_date(request)

    request.headers = {"Date": "some-unrecognizable-malformed-date-time"}
    assert not check_date(request)

    request.headers = {"X-BackendAI-Date": now.isoformat()}
    assert check_date(request)


async def test_authorize(
    etcd_fixture: None,
    database_fixture: None,
    route_deps: RouteDeps,
    create_app_and_client: Any,
    get_headers: Any,
) -> None:
    # The auth module requires config_server and database to be set up.
    mock_processors = MagicMock()
    app, client = await create_app_and_client(
        registries=[
            register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        ],
    )

    async def do_authorize(hash_type: str, api_version: str) -> None:
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
#         [register_auth_routes],
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
