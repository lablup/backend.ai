from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from ai.backend.manager.api.gql.graphql_ws.types import (
    ClientCompleteMessage,
    ClientMessage,
    ConnectionAckMessage,
    ErrorMessage,
    GQLWSMessageType,
    NextMessage,
    NextPayload,
    PingMessage,
    PongMessage,
    ServerCompleteMessage,
    SubscribeMessage,
    SubscribePayload,
)

_client_msg_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


class TestClientMessageDeserialization:
    """Discriminated union parsing for post-init client messages."""

    def test_subscribe_message(self) -> None:
        raw: dict[str, Any] = {
            "type": "subscribe",
            "id": "1",
            "payload": {"query": "subscription { events }"},
        }
        msg = _client_msg_adapter.validate_python(raw)
        assert isinstance(msg, SubscribeMessage)
        assert msg.id == "1"
        assert msg.payload.query == "subscription { events }"

    def test_subscribe_message_with_variables(self) -> None:
        raw: dict[str, Any] = {
            "type": "subscribe",
            "id": "2",
            "payload": {
                "query": "subscription($id: ID!) { events(id: $id) }",
                "variables": {"id": "abc"},
                "operationName": "Events",
            },
        }
        msg = _client_msg_adapter.validate_python(raw)
        assert isinstance(msg, SubscribeMessage)
        assert msg.payload.variables == {"id": "abc"}
        assert msg.payload.operationName == "Events"

    def test_complete_message(self) -> None:
        raw: dict[str, Any] = {"type": "complete", "id": "1"}
        msg = _client_msg_adapter.validate_python(raw)
        assert isinstance(msg, ClientCompleteMessage)
        assert msg.id == "1"

    def test_ping_message(self) -> None:
        msg = _client_msg_adapter.validate_python({"type": "ping"})
        assert isinstance(msg, PingMessage)
        assert msg.payload is None

    def test_ping_message_with_payload(self) -> None:
        msg = _client_msg_adapter.validate_python({"type": "ping", "payload": {"key": "val"}})
        assert isinstance(msg, PingMessage)
        assert msg.payload == {"key": "val"}

    def test_pong_message(self) -> None:
        msg = _client_msg_adapter.validate_python({"type": "pong"})
        assert isinstance(msg, PongMessage)

    def test_unknown_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _client_msg_adapter.validate_python({"type": "connection_ack"})

    def test_missing_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _client_msg_adapter.validate_python({"id": "1"})

    def test_subscribe_missing_payload_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _client_msg_adapter.validate_python({"type": "subscribe", "id": "1"})


class TestServerMessageSerialization:
    """Server message model_dump produces protocol-compliant dicts."""

    def test_connection_ack(self) -> None:
        msg = ConnectionAckMessage()
        d = msg.model_dump(exclude_none=True)
        assert d == {"type": GQLWSMessageType.CONNECTION_ACK}

    def test_next_message(self) -> None:
        payload = NextPayload(data={"foo": "bar"})
        msg = NextMessage(id="1", payload=payload)
        d = msg.model_dump(exclude_none=True)
        assert d == {
            "type": GQLWSMessageType.NEXT,
            "id": "1",
            "payload": {"data": {"foo": "bar"}},
        }

    def test_next_message_with_errors(self) -> None:
        payload = NextPayload(data=None, errors=[{"message": "oops"}])
        msg = NextMessage(id="1", payload=payload)
        d = msg.model_dump(exclude_none=True)
        assert d["payload"]["errors"] == [{"message": "oops"}]

    def test_error_message(self) -> None:
        msg = ErrorMessage(id="1", payload=[{"message": "bad query"}])
        d = msg.model_dump(exclude_none=True)
        assert d == {
            "type": GQLWSMessageType.ERROR,
            "id": "1",
            "payload": [{"message": "bad query"}],
        }

    def test_server_complete_message(self) -> None:
        msg = ServerCompleteMessage(id="1")
        d = msg.model_dump(exclude_none=True)
        assert d == {"type": GQLWSMessageType.COMPLETE, "id": "1"}

    def test_pong_message(self) -> None:
        msg = PongMessage()
        d = msg.model_dump(exclude_none=True)
        assert d == {"type": GQLWSMessageType.PONG}


class TestSubscribePayload:
    """SubscribePayload defaults and construction."""

    def test_minimal(self) -> None:
        p = SubscribePayload(query="{ __typename }")
        assert p.variables is None
        assert p.operationName is None

    def test_full(self) -> None:
        p = SubscribePayload(
            query="subscription { e }",
            variables={"x": 1},
            operationName="E",
        )
        assert p.variables == {"x": 1}
        assert p.operationName == "E"
