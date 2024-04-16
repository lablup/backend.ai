import json
import logging
import logging.config
import logging.handlers
import os
import pprint
import socket
import ssl
import sys
import threading
import time
import traceback
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

import coloredlogs
import graypy
import trafaret as t
import yarl
import zmq
from pythonjsonlogger.jsonlogger import JsonFormatter

from ai.backend.common import msgpack

from . import config
from . import validators as tx
from .exception import ConfigurationError
from .logging_utils import BraceStyleAdapter

# public APIs of this module
__all__ = (
    "AbstractLogger",
    "Logger",
    "NoopLogger",
    "BraceStyleAdapter",
    "LogstashHandler",
    "is_active",
    "pretty",
)

is_active: ContextVar[bool] = ContextVar("is_active", default=False)

loglevel_iv = t.Enum("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NOTSET")
logformat_iv = t.Enum("simple", "verbose")
default_pkg_ns = {
    "": "WARNING",
    "ai.backend": "INFO",
    "tests": "DEBUG",
}
logging_config_iv = t.Dict({
    t.Key("level", default="INFO"): loglevel_iv,
    t.Key("pkg-ns", default=default_pkg_ns): t.Mapping(t.String(allow_blank=True), loglevel_iv),
    t.Key("drivers", default=["console"]): t.List(t.Enum("console", "logstash", "file", "graylog")),
    t.Key(
        "console",
        default={
            "colored": None,
            "format": "verbose",
        },
    ): t.Dict({
        t.Key("colored", default=None): t.Null | t.Bool,
        t.Key("format", default="verbose"): logformat_iv,
    }).allow_extra("*"),
    t.Key("file", default=None): t.Null
    | t.Dict({
        t.Key("path"): tx.Path(type="dir", auto_create=True),
        t.Key("filename"): t.String,
        t.Key("backup-count", default=5): t.Int[1:100],
        t.Key("rotation-size", default="10M"): tx.BinarySize,
        t.Key("format", default="verbose"): logformat_iv,
    }).allow_extra("*"),
    t.Key("logstash", default=None): t.Null
    | t.Dict({
        t.Key("endpoint"): tx.HostPortPair,
        t.Key("protocol", default="tcp"): t.Enum("zmq.push", "zmq.pub", "tcp", "udp"),
        t.Key("ssl-enabled", default=True): t.Bool,
        t.Key("ssl-verify", default=True): t.Bool,
        # NOTE: logstash does not have format option.
    }).allow_extra("*"),
    t.Key("graylog", default=None): t.Null
    | t.Dict({
        t.Key("host"): t.String,
        t.Key("port"): t.ToInt[1024:65535],
        t.Key("level", default="INFO"): loglevel_iv,
        t.Key("ssl-verify", default=False): t.Bool,
        t.Key("ca-certs", default=None): t.Null | t.String(allow_blank=True),
        t.Key("keyfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("certfile", default=None): t.Null | t.String(allow_blank=True),
        t.Key("fqdn", default=True): t.Bool,
        t.Key("localname", default=None): t.Null | t.String(),
    }).allow_extra("*"),
}).allow_extra("*")


class PickledException(Exception):
    """
    Serves as a wrapper for exceptions that contain unpicklable arguments.
    """

    pass


class LogstashHandler(logging.Handler):
    def __init__(
        self,
        endpoint,
        protocol: str,
        *,
        ssl_enabled: bool = True,
        ssl_verify: bool = True,
        myhost: str = None,
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


def format_exception(self, ei):
    s = "".join(ei)
    if s[-1:] == "\n":
        s = s[:-1]
    return s


class SerializedExceptionFormatter(logging.Formatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)


class GELFTLSHandler(graypy.GELFTLSHandler):
    ssl_ctx: ssl.SSLContext

    def __init__(self, host, port=12204, validate=False, ca_certs=None, **kwargs):
        """Initialize the GELFTLSHandler

        :param host: GELF TLS input host.
        :type host: str

        :param port: GELF TLS input port.
        :type port: int

        :param validate: If :obj:`True`, validate the Graylog server's
            certificate. In this case specifying ``ca_certs`` is also
            required.
        :type validate: bool

        :param ca_certs: Path to CA bundle file.
        :type ca_certs: str
        """

        super().__init__(host, port=port, validate=validate, **kwargs)
        self.ssl_ctx = ssl.create_default_context(capath=ca_certs)
        if not validate:
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def makeSocket(self, timeout=1):
        """Create a TLS wrapped socket"""
        plain_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if hasattr(plain_socket, "settimeout"):
            plain_socket.settimeout(timeout)

        wrapped_socket = self.ssl_ctx.wrap_socket(
            plain_socket,
            server_hostname=self.host,
        )
        wrapped_socket.connect((self.host, self.port))

        return wrapped_socket


def setup_graylog_handler(config: Mapping[str, Any]) -> Optional[logging.Handler]:
    drv_config = config["graylog"]
    graylog_params = {
        "host": drv_config["host"],
        "port": drv_config["port"],
        "validate": drv_config["ssl-verify"],
        "ca_certs": drv_config["ca-certs"],
        "keyfile": drv_config["keyfile"],
        "certfile": drv_config["certfile"],
    }
    if drv_config["localname"]:
        graylog_params["localname"] = drv_config["localname"]
    else:
        graylog_params["fqdn"] = drv_config["fqdn"]

    graylog_handler = GELFTLSHandler(**graylog_params)
    graylog_handler.setLevel(config["level"])
    return graylog_handler


class ConsoleFormatter(logging.Formatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)

    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        ct = self.converter(record.created)  # type: ignore
        if datefmt:
            datefmt = datefmt.replace("%f", f"{int(record.msecs):03d}")
            return time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            return f"{t}.{int(record.msecs):03d}"


class CustomJsonFormatter(JsonFormatter):
    def formatException(self, ei) -> str:
        return format_exception(self, ei)

    def add_fields(
        self,
        log_record: dict[str, Any],  # the manipulated entry object
        record: logging.LogRecord,  # the source log record
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if loglevel := log_record.get("level"):
            log_record["level"] = loglevel.upper()
        else:
            log_record["level"] = record.levelname.upper()


class ColorizedFormatter(coloredlogs.ColoredFormatter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        coloredlogs.logging.Formatter.formatException = format_exception


class pretty:
    """A simple object wrapper to pretty-format it when formatting the log record."""

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def __repr__(self) -> str:
        return pprint.pformat(self.obj)


def setup_console_log_handler(config: Mapping[str, Any]) -> logging.Handler:
    log_formats = {
        "simple": "%(levelname)s %(message)s",
        "verbose": "%(asctime)s %(levelname)s %(name)s [%(process)d] %(message)s",
    }
    drv_config = config["console"]
    console_formatter: logging.Formatter
    colored = drv_config["colored"]
    if colored is None:
        colored = sys.stderr.isatty()
    if colored:
        console_formatter = ColorizedFormatter(
            log_formats[drv_config["format"]],
            datefmt="%Y-%m-%d %H:%M:%S.%f",  # coloredlogs has intrinsic support for msec
            field_styles={
                "levelname": {"color": 248, "bold": True},
                "name": {"color": 246, "bold": False},
                "process": {"color": "cyan"},
                "asctime": {"color": 240},
            },
            level_styles={
                "debug": {"color": "green"},
                "verbose": {"color": "green", "bright": True},
                "info": {"color": "cyan", "bright": True},
                "notice": {"color": "cyan", "bold": True},
                "warning": {"color": "yellow"},
                "error": {"color": "red", "bright": True},
                "success": {"color": 77},
                "critical": {"background": "red", "color": 255, "bold": True},
            },
        )
    else:
        console_formatter = ConsoleFormatter(
            log_formats[drv_config["format"]],
            datefmt="%Y-%m-%d %H:%M:%S.%f",
        )
    console_handler = logging.StreamHandler(
        stream=sys.stderr,
    )
    console_handler.setLevel(config["level"])
    console_handler.setFormatter(console_formatter)
    return console_handler


def setup_file_log_handler(config: Mapping[str, Any]) -> logging.Handler:
    drv_config = config["file"]
    fmt = "%(timestamp) %(level) %(name) %(processName) %(message)"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=drv_config["path"] / drv_config["filename"],
        backupCount=drv_config["backup-count"],
        maxBytes=drv_config["rotation-size"],
        encoding="utf-8",
    )
    file_handler.setLevel(config["level"])
    file_handler.setFormatter(CustomJsonFormatter(fmt))
    return file_handler


def log_worker(
    logging_config: Mapping[str, Any],
    parent_pid: int,
    log_endpoint: str,
    ready_event: threading.Event,
) -> None:
    console_handler = None
    file_handler = None
    logstash_handler = None
    graylog_handler = None

    # For future references: when implementing new kind of logging adapters,
    # make sure to adapt our custom `Formatter.formatException()` approach;
    # Otherwise it won't print out EXCEPTION level log (along with the traceback).
    if "console" in logging_config["drivers"]:
        console_handler = setup_console_log_handler(logging_config)

    if "file" in logging_config["drivers"]:
        file_handler = setup_file_log_handler(logging_config)

    if "logstash" in logging_config["drivers"]:
        drv_config = logging_config["logstash"]
        logstash_handler = LogstashHandler(
            endpoint=drv_config["endpoint"],
            protocol=drv_config["protocol"],
            ssl_enabled=drv_config["ssl-enabled"],
            ssl_verify=drv_config["ssl-verify"],
            myhost="hostname",  # TODO: implement
        )
        logstash_handler.setLevel(logging_config["level"])
        logstash_handler.setFormatter(SerializedExceptionFormatter())
    if "graylog" in logging_config["drivers"]:
        graylog_handler = setup_graylog_handler(logging_config)
        assert graylog_handler is not None
        graylog_handler.setFormatter(SerializedExceptionFormatter())

    zctx = zmq.Context()
    agg_sock = zctx.socket(zmq.PULL)
    agg_sock.bind(log_endpoint)
    ep_url = yarl.URL(log_endpoint)
    if ep_url.scheme.lower() == "ipc":
        os.chmod(ep_url.path, 0o777)
    try:
        ready_event.set()
        while True:
            data = agg_sock.recv()
            if not data:
                return
            unpacked_data = msgpack.unpackb(data)
            if not unpacked_data:
                break
            rec = logging.makeLogRecord(unpacked_data)
            if rec is None:
                break
            if console_handler:
                console_handler.emit(rec)
            try:
                if file_handler:
                    file_handler.emit(rec)
                if logstash_handler:
                    logstash_handler.emit(rec)
                    print("logstash")
                if graylog_handler:
                    graylog_handler.emit(rec)
            except OSError:
                # don't terminate the log worker.
                continue
    finally:
        if logstash_handler:
            logstash_handler.cleanup()
        if graylog_handler:
            graylog_handler.close()
        agg_sock.close()
        zctx.term()


class RelayHandler(logging.Handler):
    _sock: zmq.Socket | None

    def __init__(self, *, endpoint: str) -> None:
        super().__init__()
        self.endpoint = endpoint
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
            serialized_record = msgpack.packb(log_body)
            self._sock.send(serialized_record)
        except zmq.ZMQError:
            self._fallback(record)


class AbstractLogger(metaclass=ABCMeta):
    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
    ) -> None:
        pass

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, *exc_info_args):
        raise NotImplementedError


class NoopLogger(AbstractLogger):
    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
    ) -> None:
        pass

    def __enter__(self):
        pass

    def __exit__(self, *exc_info_args):
        pass


class LocalLogger(AbstractLogger):
    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
    ) -> None:
        cfg = logging_config_iv.check(logging_config)
        _check_driver_config_exists_if_activated(cfg, "console")
        self.logging_config = cfg
        log_handlers = []
        if "console" in self.logging_config["drivers"]:
            console_handler = setup_console_log_handler(self.logging_config)
            log_handlers.append(console_handler)
        if "file" in self.logging_config["drivers"]:
            file_handler = setup_file_log_handler(self.logging_config)
            log_handlers.append(file_handler)
        self.log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "null": {"class": "logging.NullHandler"},
            },
            "loggers": {
                "": {
                    "handlers": [],
                    "level": cfg["level"],
                },
                **{
                    k: {
                        "handlers": [],
                        "level": v,
                        "propagate": False,
                    }
                    for k, v in cfg["pkg-ns"].items()
                },
            },
        }
        logging.config.dictConfig(self.log_config)
        root_logger = logging.getLogger(None)
        for h in log_handlers:
            root_logger.addHandler(h)
        for pkg_ns in cfg["pkg-ns"].keys():
            ns_logger = logging.getLogger(pkg_ns)
            for h in log_handlers:
                ns_logger.addHandler(h)

    def __enter__(self):
        pass

    def __exit__(self, *exc_info_args):
        pass


class Logger(AbstractLogger):
    is_master: bool
    log_endpoint: str
    logging_config: Mapping[str, Any]
    log_config: MutableMapping[str, Any]
    log_worker: threading.Thread

    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
        *,
        is_master: bool,
        log_endpoint: str,
    ) -> None:
        legacy_logfile_path = os.environ.get("BACKEND_LOG_FILE")
        if legacy_logfile_path:
            p = Path(legacy_logfile_path)
            config.override_key(logging_config, ("file", "path"), p.parent)
            config.override_key(logging_config, ("file", "filename"), p.name)
        config.override_with_env(logging_config, ("file", "backup-count"), "BACKEND_LOG_FILE_COUNT")
        legacy_logfile_size = os.environ.get("BACKEND_LOG_FILE_SIZE")
        if legacy_logfile_size:
            legacy_logfile_size = f"{legacy_logfile_size}M"
            config.override_with_env(logging_config, ("file", "rotation-size"), legacy_logfile_size)

        cfg = logging_config_iv.check(logging_config)

        _check_driver_config_exists_if_activated(cfg, "console")
        _check_driver_config_exists_if_activated(cfg, "file")
        _check_driver_config_exists_if_activated(cfg, "logstash")
        _check_driver_config_exists_if_activated(cfg, "graylog")

        self.is_master = is_master
        self.log_endpoint = log_endpoint
        self.logging_config = cfg
        self.log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "null": {"class": "logging.NullHandler"},
            },
            "loggers": {
                "": {"handlers": [], "level": cfg["level"]},
                **{
                    k: {"handlers": [], "level": v, "propagate": False}
                    for k, v in cfg["pkg-ns"].items()
                },
            },
        }

    def __enter__(self):
        self.log_config["handlers"]["relay"] = {
            "class": "ai.backend.common.logging.RelayHandler",
            "level": self.logging_config["level"],
            "endpoint": self.log_endpoint,
        }
        for _logger in self.log_config["loggers"].values():
            _logger["handlers"].append("relay")
        logging.config.dictConfig(self.log_config)
        self._is_active_token = is_active.set(True)
        if self.is_master and self.log_endpoint:
            self.relay_handler = logging.getLogger("").handlers[0]
            self.ready_event = threading.Event()
            assert isinstance(self.relay_handler, RelayHandler)
            self.log_worker = threading.Thread(
                target=log_worker,
                name="Logger",
                args=(self.logging_config, os.getpid(), self.log_endpoint, self.ready_event),
            )
            self.log_worker.start()
            self.ready_event.wait()

    def __exit__(self, *exc_info_args):
        # Resetting generates "different context" errors.
        # Since practically we only need to check activeness in alembic scripts
        # and it should be active until the program terminates,
        # just leave it as-is.
        is_active.reset(self._is_active_token)
        if self.is_master and self.log_endpoint:
            self.relay_handler.emit(None)
            self.log_worker.join()
            self.relay_handler.close()
            ep_url = yarl.URL(self.log_endpoint)
            if ep_url.scheme.lower() == "ipc" and (ep_sock := Path(ep_url.path)).exists():
                ep_sock.unlink()


def _check_driver_config_exists_if_activated(cfg, driver):
    if driver in cfg["drivers"] and cfg[driver] is None:
        raise ConfigurationError({"logging": f"{driver} driver is activated but no config given."})
