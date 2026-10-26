from __future__ import annotations

import logging
import os
import sys
import traceback
from typing import TYPE_CHECKING, Any, override

import msgpack
import psutil
import zmq

from ai.backend.logging.formatter import message_with_log_fields
from ai.backend.logging.structured import LogFieldNormalizer

if TYPE_CHECKING:
    from ai.backend.logging.types import MsgpackOptions


class RelayHandler(logging.Handler):
    _sock: zmq.Socket[Any] | None
    _normalizer: LogFieldNormalizer

    def __init__(self, *, endpoint: str, msgpack_options: MsgpackOptions) -> None:
        super().__init__()
        self.endpoint = endpoint
        self.msgpack_options = msgpack_options
        self._zctx = zmq.Context[zmq.Socket[Any]]()
        self._pid = os.getpid()
        self._process_name = psutil.Process().name()
        self._normalizer = LogFieldNormalizer()
        # We should use PUSH-PULL socket pairs to avoid
        # lost of synchronization sentinel messages.
        if endpoint:
            self._sock = self._zctx.socket(zmq.PUSH)
            if self._sock is None:
                raise RuntimeError("Failed to create ZMQ PUSH socket")
            self._sock.setsockopt(zmq.LINGER, 100)
            self._sock.connect(self.endpoint)
        else:
            self._sock = None

    @override
    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
        self._zctx.term()

    def _print_to_stderr(self, record: logging.LogRecord | None) -> None:
        if record is None:
            return
        print(
            message_with_log_fields(record.getMessage(), record, self._normalizer), file=sys.stderr
        )

    @override
    def emit(self, record: logging.LogRecord | None) -> None:
        if self._sock is None:
            self._print_to_stderr(record)
            return
        # record may be None to signal shutdown.
        log_body: dict[str, object] | None
        if record:
            log_body = {
                "name": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "msg": record.getMessage(),
                "levelno": record.levelno,
                "levelname": record.levelname,
                "process": self._pid,
                "processName": self._process_name,
                **self._normalizer.normalized_fields_of(record),
            }
            if record.exc_info:
                log_body["exc_info"] = traceback.format_exception(*record.exc_info)
        else:
            log_body = None
        try:
            serialized_record = msgpack.packb(log_body, **self.msgpack_options["pack_opts"])
            self._sock.send(serialized_record)
        except zmq.ZMQError:
            self._print_to_stderr(record)
