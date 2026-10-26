import logging
from collections.abc import Iterator
from typing import Any

import pytest
import zmq

from ai.backend.common import msgpack
from ai.backend.logging.handler.intrinsic import RelayHandler
from ai.backend.logging.types import MsgpackOptions

_MSGPACK_OPTIONS: MsgpackOptions = {
    "pack_opts": msgpack.DEFAULT_PACK_OPTS,
    "unpack_opts": msgpack.DEFAULT_UNPACK_OPTS,
}


@pytest.fixture
def parent_socket() -> Iterator[zmq.Socket[Any]]:
    zmq_context = zmq.Context[zmq.Socket[Any]]()
    pull_socket = zmq_context.socket(zmq.PULL)
    pull_socket.setsockopt(zmq.RCVTIMEO, 5000)
    yield pull_socket
    pull_socket.close(linger=0)
    zmq_context.term()


@pytest.fixture
def relay_handler(parent_socket: zmq.Socket[Any]) -> Iterator[RelayHandler]:
    port = parent_socket.bind_to_random_port("tcp://127.0.0.1")
    connected_handler = RelayHandler(
        endpoint=f"tcp://127.0.0.1:{port}", msgpack_options=_MSGPACK_OPTIONS
    )
    yield connected_handler
    connected_handler.close()


@pytest.fixture
def socketless_relay_handler() -> Iterator[RelayHandler]:
    socketless_handler = RelayHandler(endpoint="", msgpack_options=_MSGPACK_OPTIONS)
    yield socketless_handler
    socketless_handler.close()


class TestRelayHandler:
    def test_structured_fields_reach_parent(
        self,
        relay_handler: RelayHandler,
        parent_socket: zmq.Socket[Any],
        structured_record: logging.LogRecord,
    ) -> None:
        relay_handler.emit(structured_record)

        relayed_record = logging.makeLogRecord(msgpack.unpackb(parent_socket.recv()))
        assert relayed_record.getMessage() == "image pull retried"
        assert relayed_record.__dict__["log_tag_kernel_id"] == "kernel-1"
        assert relayed_record.__dict__["log_tag_attempt"] == 3

    def test_fallback_prints_fields(
        self,
        socketless_relay_handler: RelayHandler,
        structured_record: logging.LogRecord,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        socketless_relay_handler.emit(structured_record)

        assert capsys.readouterr().err == "image pull retried kernel_id=kernel-1 attempt=3\n"
