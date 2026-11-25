from __future__ import annotations

import logging
import socket
import sys
from dataclasses import dataclass
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_KEEPALIVE_IDLE_OPT: int | None = getattr(
    socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None)
)
_KEEPALIVE_INTERVAL_OPT: int | None = getattr(socket, "TCP_KEEPINTVL", None)
_KEEPALIVE_COUNT_OPT: int | None = getattr(socket, "TCP_KEEPCNT", None)
_USER_TIMEOUT_OPT: int | None = (
    getattr(socket, "TCP_USER_TIMEOUT", None) if sys.platform.startswith("linux") else None
)


@dataclass(frozen=True)
class TCPOptions:
    """TCP options of a database connection socket, in seconds."""

    keepalive_idle: int
    keepalive_interval: int
    keepalive_count: int
    user_timeout: int

    def apply(self, sock: Any) -> None:
        """
        Sets the options the platform has on a connected socket.
        A failure is logged as a warning, as the connection works without the options.
        """
        if sock.family not in (socket.AF_INET, socket.AF_INET6):
            return
        options: list[tuple[int, int, int]] = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
        if _KEEPALIVE_IDLE_OPT is not None:
            options.append((socket.IPPROTO_TCP, _KEEPALIVE_IDLE_OPT, self.keepalive_idle))
        if _KEEPALIVE_INTERVAL_OPT is not None:
            options.append((socket.IPPROTO_TCP, _KEEPALIVE_INTERVAL_OPT, self.keepalive_interval))
        if _KEEPALIVE_COUNT_OPT is not None:
            options.append((socket.IPPROTO_TCP, _KEEPALIVE_COUNT_OPT, self.keepalive_count))
        if _USER_TIMEOUT_OPT is not None:
            options.append((socket.IPPROTO_TCP, _USER_TIMEOUT_OPT, self.user_timeout * 1000))
        for level, name, value in options:
            try:
                sock.setsockopt(level, name, value)
            except OSError as e:
                log.warning("database socket option not set (option: {}, reason: {!r})", name, e)
