from __future__ import annotations

import json
import logging
import socket
import ssl
from collections import OrderedDict
from datetime import datetime

import zmq

from ..exceptions import ConfigurationError


class LogstashHandler(logging.Handler):
    def __init__(
        self,
        endpoint,
        protocol: str,
        *,
        ssl_enabled: bool = True,
        ssl_verify: bool = True,
        myhost: str | None = None,
    ):
        super().__init__()
        self._endpoint = endpoint
        self._protocol = protocol
        self._ssl_enabled = ssl_enabled
        self._ssl_verify = ssl_verify
        self._myhost = myhost
        self._sock = None
        self._sslctx = None
        self._zmqctx = None

    def _setup_transport(self):
        if self._sock is not None:
            return
        if self._protocol == "zmq.push":
            self._zmqctx = zmq.Context()
            sock = self._zmqctx.socket(zmq.PUSH)
            sock.setsockopt(zmq.LINGER, 50)
            sock.setsockopt(zmq.SNDHWM, 20)
            sock.connect(f"tcp://{self._endpoint[0]}:{self._endpoint[1]}")
            self._sock = sock
        elif self._protocol == "zmq.pub":
            self._zmqctx = zmq.Context()
            sock = self._zmqctx.socket(zmq.PUB)
            sock.setsockopt(zmq.LINGER, 50)
            sock.setsockopt(zmq.SNDHWM, 20)
            sock.connect(f"tcp://{self._endpoint[0]}:{self._endpoint[1]}")
            self._sock = sock
        elif self._protocol == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self._ssl_enabled:
                self._sslctx = ssl.create_default_context()
                if not self._ssl_verify:
                    self._sslctx.check_hostname = False
                    self._sslctx.verify_mode = ssl.CERT_NONE
                sock = self._sslctx.wrap_socket(sock, server_hostname=self._endpoint[0])
            sock.connect((str(self._endpoint.host), self._endpoint.port))
            self._sock = sock
        elif self._protocol == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((str(self._endpoint.host), self._endpoint.port))
            self._sock = sock
        else:
            raise ConfigurationError({
                "logging.LogstashHandler": f"unsupported protocol: {self._protocol}"
            })

    def cleanup(self):
        if self._sock:
            self._sock.close()
        self._sslctx = None
        if self._zmqctx:
            self._zmqctx.term()

    def emit(self, record):
        self._setup_transport()
        tags = set()
        extra_data = dict()

        # This log format follows logstash's event format.
        log = OrderedDict([
            ("@timestamp", datetime.now().isoformat()),
            ("@version", 1),
            ("host", self._myhost),
            ("logger", record.name),
            ("path", record.pathname),
            ("func", record.funcName),
            ("lineno", record.lineno),
            ("message", record.getMessage()),
            ("level", record.levelname),
            ("tags", list(tags)),
        ])
        log.update(extra_data)
        if self._protocol.startswith("zmq"):
            self._sock.send_json(log)
        else:
            # TODO: reconnect if disconnected
            self._sock.sendall(json.dumps(log).encode("utf-8"))
