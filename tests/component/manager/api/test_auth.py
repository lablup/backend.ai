from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from dateutil.tz import gettz, tzutc

from ai.backend.manager.api.rest.middleware.auth import _extract_auth_params, check_date
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
