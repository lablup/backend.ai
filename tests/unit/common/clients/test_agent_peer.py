from __future__ import annotations

import uuid
from typing import Any, cast

from callosum.rpc import Peer

from ai.backend.common.clients.agent.peer import PeerInvoker
from ai.backend.common.contexts.request_id import with_request_context
from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole


class _RecordingPeer:
    bodies: list[dict[str, Any]]
    last_used: float

    def __init__(self) -> None:
        self.bodies = []
        self.last_used = 0.0

    async def invoke(self, name: str, body: dict[str, Any], *, order_key: str | None) -> None:
        self.bodies.append(body)


def _user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


async def test_call_carries_request_and_user_metadata() -> None:
    peer = _RecordingPeer()
    stub = PeerInvoker._CallStub(cast(Peer, peer))
    user = _user()
    request_id = str(uuid.uuid4())

    with with_request_context(request_id), with_user_context(user, user):
        await stub.destroy_kernel("k", "s", agent_id="i-test")

    body = peer.bodies[0]
    assert body["args"] == ("k", "s")
    assert body["kwargs"] == {"agent_id": "i-test"}
    assert body["metadata"]["request_id"] == request_id
    assert body["metadata"]["user"]["user_id"] == str(user.user_id)
    assert body["metadata"]["triggered_user"]["user_id"] == str(user.user_id)


async def test_call_without_context_carries_empty_metadata() -> None:
    peer = _RecordingPeer()
    stub = PeerInvoker._CallStub(cast(Peer, peer))

    await stub.ping("ping")

    assert peer.bodies[0]["metadata"] == {
        "request_id": None,
        "user": None,
        "triggered_user": None,
        "traceparent": None,
    }
