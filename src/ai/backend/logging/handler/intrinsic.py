from __future__ import annotations

import logging
import sys
import traceback
from collections.abc import Mapping
from typing import Any, Optional, override

import msgpack
import zmq


class RelayHandler(logging.Handler):
    _sock: zmq.Socket | None

    def __init__(self, *, endpoint: str, msgpack_options: Mapping[str, Any]) -> None:
        super().__init__()
        self.endpoint = endpoint
        self.msgpack_options = msgpack_options
        self._zctx = zmq.Context()
        # We should use PUSH-PULL socket pairs to avoid
        # lost of synchronization sentinel messages.
        if endpoint:
            self._sock = self._zctx.socket(zmq.PUSH)
            assert self._sock is not None
            self._sock.setsockopt(zmq.LINGER, 100)
            self._sock.connect(self.endpoint)
        else:
            self._sock = None

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
        self._zctx.term()

    def _fallback(self, record: Optional[logging.LogRecord]) -> None:
        if record is None:
            return
        print(record.getMessage(), file=sys.stderr)

    @override
    def emit(self, record: Optional[logging.LogRecord]) -> None:
        if self._sock is None:
            self._fallback(record)
            return
        # record may be None to signal shutdown.
        if record:
            log_body = {
                "name": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "msg": record.getMessage(),
                "levelno": record.levelno,
                "levelname": record.levelname,
            }
            if record.exc_info:
                log_body["exc_info"] = traceback.format_exception(*record.exc_info)
        else:
            log_body = None
        try:
            serialized_record = msgpack.packb(log_body, **self.msgpack_options)
            self._sock.send(serialized_record)
        except zmq.ZMQError:
            self._fallback(record)
