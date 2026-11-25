from __future__ import annotations

import socket
import sys
from typing import Any

import pytest

from ai.backend.common.db.connector import PrimaryMemberConnector
from ai.backend.common.db.socket_options import TCPOptions
from ai.backend.common.typed_validators import HostPortPair

# Matches the credentials of the `postgres_container` fixture.
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "develove"
POSTGRES_MAINTENANCE_DB = "testing"

OPTIONS = TCPOptions(
    keepalive_idle=7,
    keepalive_interval=3,
    keepalive_count=4,
    user_timeout=11,
)


class _FailingSocket:
    family = socket.AF_INET

    def setsockopt(self, *_args: Any) -> None:
        raise OSError("not supported")


class TestTCPOptions:
    async def test_connected_socket_has_the_options(
        self,
        postgres_container: tuple[str, HostPortPair],
    ) -> None:
        _, addr = postgres_container
        connector = PrimaryMemberConnector(
            [(addr.host, addr.port)],
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_MAINTENANCE_DB,
            connect_timeout=5,
            connect_kwargs={},
            tcp_options=OPTIONS,
        )
        conn = await connector.connect()
        try:
            sock = conn._transport.get_extra_info("socket")
            assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) != 0
            idle_opt = getattr(socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None))
            expected: list[tuple[int | None, int]] = [
                (idle_opt, OPTIONS.keepalive_idle),
                (getattr(socket, "TCP_KEEPINTVL", None), OPTIONS.keepalive_interval),
                (getattr(socket, "TCP_KEEPCNT", None), OPTIONS.keepalive_count),
            ]
            if sys.platform.startswith("linux"):
                expected.append((
                    getattr(socket, "TCP_USER_TIMEOUT", None),
                    OPTIONS.user_timeout * 1000,
                ))
            checked = 0
            for opt, value in expected:
                if opt is None:
                    continue
                assert sock.getsockopt(socket.IPPROTO_TCP, opt) == value
                checked += 1
            assert checked > 0
        finally:
            await conn.close()

    def test_failure_to_set_an_option_does_not_raise(self) -> None:
        OPTIONS.apply(_FailingSocket())

    @pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="requires AF_UNIX")
    def test_non_tcp_socket_is_left_alone(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            OPTIONS.apply(sock)
            assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) == 0
        finally:
            sock.close()
