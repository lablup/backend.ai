from __future__ import annotations

import logging
import logging.config
import logging.handlers
import os
import sys
import threading
from collections.abc import Mapping, MutableMapping
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Self, TypedDict, override

import msgpack
import yarl
import zmq

from .abc import AbstractLogger
from .config import logging_config_iv, override_key
from .exceptions import ConfigurationError
from .formatter import (
    ColorizedFormatter,
    ConsoleFormatter,
    CustomJsonFormatter,
    SerializedExceptionFormatter,
)
from .handler.intrinsic import RelayHandler

is_active: ContextVar[bool] = ContextVar("is_active", default=False)


def _check_driver_config_exists_if_activated(cfg, driver):
    if driver in cfg["drivers"] and cfg[driver] is None:
        raise ConfigurationError({"logging": f"{driver} driver is activated but no config given."})


class MsgpackOptions(TypedDict):
    pack_opts: Mapping[str, Any]
    unpack_opts: Mapping[str, Any]


class NoopLogger(AbstractLogger):
    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
    ) -> None:
        pass

    @override
    def __enter__(self) -> Self:
        return self

    @override
    def __exit__(self, *exc_info_args) -> bool | None:
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

    @override
    def __enter__(self) -> Self:
        return self

    @override
    def __exit__(self, *exc_info_args) -> bool | None:
        pass


class Logger(AbstractLogger):
    is_master: bool
    log_endpoint: str
    logging_config: Mapping[str, Any]
    log_config: dict[str, Any]
    log_worker: threading.Thread

    def __init__(
        self,
        logging_config: MutableMapping[str, Any],
        *,
        is_master: bool,
        log_endpoint: str,
        msgpack_options: MsgpackOptions,
    ) -> None:
        if (env_legacy_logfile_path := os.environ.get("BACKEND_LOG_FILE", None)) is not None:
            p = Path(env_legacy_logfile_path)
            override_key(logging_config, ("file", "path"), p.parent)
            override_key(logging_config, ("file", "filename"), p.name)
        if (env_legacy_backup_count := os.environ.get("BACKEND_LOG_FILE_COUNT", None)) is not None:
            override_key(logging_config, ("file", "backup-count"), env_legacy_backup_count)
        if (env_legacy_logfile_size := os.environ.get("BACKEND_LOG_FILE_SIZE", None)) is not None:
            legacy_logfile_size = f"{env_legacy_logfile_size}M"
            override_key(logging_config, ("file", "rotation-size"), legacy_logfile_size)

        cfg = logging_config_iv.check(logging_config)

        _check_driver_config_exists_if_activated(cfg, "console")
        _check_driver_config_exists_if_activated(cfg, "file")
        _check_driver_config_exists_if_activated(cfg, "logstash")
        _check_driver_config_exists_if_activated(cfg, "graylog")

        self.is_master = is_master
        self.msgpack_options = msgpack_options
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

    @override
    def __enter__(self) -> Self:
        self.log_config["handlers"]["relay"] = {
            "class": "ai.backend.logging.handler.intrinsic.RelayHandler",
            "level": self.logging_config["level"],
            "endpoint": self.log_endpoint,
            "msgpack_options": self.msgpack_options,
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
                args=(
                    self.logging_config,
                    os.getpid(),
                    self.log_endpoint,
                    self.ready_event,
                    self.msgpack_options,
                ),
            )
            self.log_worker.start()
            self.ready_event.wait()
        return self

    @override
    def __exit__(self, *exc_info_args) -> bool | None:
        # Resetting generates "different context" errors.
        # Since practically we only need to check activeness in alembic scripts
        # and it should be active until the program terminates,
        # just leave it as-is.
        is_active.reset(self._is_active_token)
        if self.is_master and self.log_endpoint:
            assert isinstance(self.relay_handler, RelayHandler)
            self.relay_handler.emit(None)
            self.log_worker.join()
            self.relay_handler.close()
            ep_url = yarl.URL(self.log_endpoint)
            if ep_url.scheme.lower() == "ipc" and (ep_sock := Path(ep_url.path)).exists():
                ep_sock.unlink()
        return None


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
    msgpack_options: MsgpackOptions,
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
        from .handler.logstash import LogstashHandler

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
        from .handler.graylog import setup_graylog_handler

        graylog_handler = setup_graylog_handler(logging_config)
        assert graylog_handler is not None
        graylog_handler.setFormatter(SerializedExceptionFormatter())

    zctx = zmq.Context[zmq.Socket]()
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
            unpacked_data = msgpack.unpackb(data, **msgpack_options["unpack_opts"])
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
