import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from dateutil.tz import gettz, tzutc

from ai.backend.manager.api.auth import _extract_auth_params, check_date
from ai.backend.manager.api.exceptions import InvalidAuthParameters
from ai.backend.manager.server import (
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    shared_config_ctx,
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
async def test_authorize(etcd_fixture, database_fixture, create_app_and_client, get_headers):
    # The auth module requires config_server and database to be set up.
    app, client = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
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
