import uuid

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.request import Request
from ai.backend.client.session import AsyncSession, Session

# module-level marker
pytestmark = pytest.mark.integration


def test_auth():
    random_msg = uuid.uuid4().hex
    with Session():
        request = Request("GET", "/auth")
        request.set_json({
            "echo": random_msg,
        })
        with request.fetch() as resp:
            assert resp.status == 200
            data = resp.json()
            assert data["authorized"] == "yes"
            assert data["echo"] == random_msg


def test_auth_missing_signature(monkeypatch):
    random_msg = uuid.uuid4().hex
    with Session():
        rqst = Request("GET", "/auth")
        rqst.set_json({"echo": random_msg})
        # let it bypass actual signing
        from ai.backend.client import request

        noop_sign = lambda *args, **kwargs: ({}, None)
        monkeypatch.setattr(request, "generate_signature", noop_sign)
        with pytest.raises(BackendAPIError) as e:
            with rqst.fetch():
                pass
        assert e.value.status == 401


def test_auth_malformed():
    with Session():
        request = Request("GET", "/auth")
        request.set_content(
            b"<this is not json>",
            content_type="application/json",
        )
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 400


def test_auth_missing_body():
    with Session():
        request = Request("GET", "/auth")
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 400


@pytest.mark.asyncio
async def test_async_auth():
    random_msg = uuid.uuid4().hex
    async with AsyncSession():
        request = Request("GET", "/auth")
        request.set_json({
            "echo": random_msg,
        })
        async with request.fetch() as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["authorized"] == "yes"
            assert data["echo"] == random_msg
