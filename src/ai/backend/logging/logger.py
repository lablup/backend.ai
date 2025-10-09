from __future__ import annotations

import contextlib
import logging
import logging.config
import logging.handlers
import os
import sys
import threading
from collections.abc import Iterator
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, Self, override

import msgpack
import yarl
import zmq
from glide.exceptions import ConfigurationError
from pydantic import ByteSize

from ai.backend.common.typed_validators import AutoDirectoryPath

from .abc import AbstractLogger
from .config import (
    LoggerConfig,
    LoggingConfig,
    LogHandlerConfig,
    RelayLogHandlerConfig,
    default_pkg_ns,
)
from .formatter import (
    ColorizedFormatter,
    ConsoleFormatter,
    CustomJsonFormatter,
    SerializedExceptionFormatter,
)
from .handler.intrinsic import RelayHandler
from .types import LogLevel, MsgpackOptions
from .utils import _register_custom_loglevels

is_active: ContextVar[bool] = ContextVar("is_active", default=False)
_register_custom_loglevels()


class NoopLogger(AbstractLogger):
    def __init__(self, config: LoggingConfig) -> None:
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
        config: Optional[LoggingConfig] = None,
        *,
        log_level: LogLevel = LogLevel.NOTSET,
    ) -> None:
        """
        Sets up a simple local logger using only console and file handlers for CLI command implementations.

        The caller may pass a full config or just the log-level set via an CLI option, which will create a default LoggingConfig based on it.
        If config is given, log_level is used to override the log-level of the final filter and the "ai.backend" namespace.
        """
        if config is None:
            self.config = LoggingConfig(
                disable_existing_loggers=False,
                handlers={
                    "null": LogHandlerConfig(class_="logging.NullHandler"),
                },
                loggers={
                    **{
                        k: LoggerConfig(
                            handlers=[],
                            level=v,
                            propagate=False,
                        )
                        for k, v in default_pkg_ns.items()
                    },
                },
            )
        else:
            self.config = config
        if log_level != LogLevel.NOTSET:
            self.config.level = log_level
            self.config.pkg_ns["ai.backend"] = log_level
        logging.config.dictConfig(self.config.model_dump())

    @override
    def __enter__(self) -> Self:
        self.handler_stack = contextlib.ExitStack()
        log_handlers: list[logging.Handler] = []
        if "console" in self.config.drivers:
            log_handlers.append(
                self.handler_stack.enter_context(setup_console_log_handler(self.config))
            )
        if "file" in self.config.drivers:
            log_handlers.append(
                self.handler_stack.enter_context(setup_file_log_handler(self.config))
            )
        root_logger = logging.getLogger(None)
        for h in log_handlers:
            root_logger.addHandler(h)
            root_logger.setLevel(self.config.level)
        for pkg_ns in self.config.pkg_ns.keys():
            ns_logger = logging.getLogger(pkg_ns)
            for h in log_handlers:
                ns_logger.addHandler(h)
        return self

    @override
    def __exit__(self, *exc_info_args) -> bool | None:
        self.handler_stack.close()
        return None


class Logger(AbstractLogger):
    is_master: bool
    log_endpoint: str
    parent_logging_config: LoggingConfig
    worker_logging_config: LoggingConfig
    log_processor: threading.Thread

    def __init__(
        self,
        config: LoggingConfig,
        *,
        is_master: bool,
        log_endpoint: str,
        msgpack_options: MsgpackOptions,
    ) -> None:
        self.is_master = is_master
        self.msgpack_options = msgpack_options
        self.log_endpoint = log_endpoint
        self.parent_logging_config = config
        # Let the workers inherit the per-package logger and level configurations from the parent.
        # Each worker will add the RelayHandler by themselves.
        self.worker_logging_config = LoggingConfig(
            # version=1,
            disable_existing_loggers=False,
            handlers={
                "null": LogHandlerConfig(class_="logging.NullHandler"),
            },
            level=config.level,
            loggers={
                "": LoggerConfig(handlers=[], level=config.level),
                **{
                    k: LoggerConfig(handlers=[], level=v, propagate=False)
                    for k, v in config.pkg_ns.items()
                },
            },
        )

    @override
    def __enter__(self) -> Self:
        # Including the parent itself, each service process has its own RelayHandler
        # to send the log records to the log processor thread in the parent process.
        self.worker_logging_config.handlers["relay"] = RelayLogHandlerConfig(
            class_="ai.backend.logging.handler.intrinsic.RelayHandler",
            level=self.parent_logging_config.level,
            endpoint=self.log_endpoint,
            msgpack_options=self.msgpack_options,
        )
        for _logger in self.worker_logging_config.loggers.values():
            _logger.handlers.append("relay")
        logging.config.dictConfig(self.worker_logging_config.model_dump())
        self._is_active_token = is_active.set(True)
        if self.is_master and self.log_endpoint:
            self.relay_handler = logging.getLogger("").handlers[0]
            self.ready_event = threading.Event()
            assert isinstance(self.relay_handler, RelayHandler)
            self.log_processor = threading.Thread(
                target=log_processor,
                name="Logger",
                args=(
                    self.parent_logging_config,
                    os.getpid(),
                    self.log_endpoint,
                    self.ready_event,
                    self.msgpack_options,
                ),
            )
            self.log_processor.start()
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
            self.relay_handler.emit(None)  # sentinel to stop log_processor
            self.log_processor.join()
            self.relay_handler.close()
            ep_url = yarl.URL(self.log_endpoint)
            if ep_url.scheme.lower() == "ipc" and (ep_sock := Path(ep_url.path)).exists():
                ep_sock.unlink()
        return None


@contextlib.contextmanager
def setup_console_log_handler(config: LoggingConfig) -> Iterator[logging.Handler]:
    log_formats = {
        "simple": "%(levelname)s %(message)s",
        "verbose": "%(asctime)s %(levelname)s %(name)s [%(process)d] %(message)s",
    }
    drv_config = config.console
    console_formatter: logging.Formatter
    colored = drv_config.colored
    if colored is None:
        colored = sys.stderr.isatty()
    if colored:
        console_formatter = ColorizedFormatter(
            log_formats[drv_config.format],
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
            log_formats[drv_config.format],
            datefmt="%Y-%m-%d %H:%M:%S.%f",
        )
    console_handler = logging.StreamHandler(
        stream=sys.stderr,
    )
    console_handler.setLevel(config.level)
    console_handler.setFormatter(console_formatter)
    yield console_handler


@contextlib.contextmanager
def setup_file_log_handler(config: LoggingConfig) -> Iterator[logging.Handler]:
    if config.file is None:
        raise ConfigurationError(
            "logging.setup_file_log_handler: "
            "The 'file' logging driver is active but its config is missing"
        )

    # FIXME: Refactor using layered config loader pattern
    if (env_legacy_logfile_path := os.environ.get("BACKEND_LOG_FILE", None)) is not None:
        p = Path(env_legacy_logfile_path)
        config.file.path = AutoDirectoryPath(p.parent)
        config.file.filename = p.name
    if (env_legacy_backup_count := os.environ.get("BACKEND_LOG_FILE_COUNT", None)) is not None:
        config.file.backup_count = int(env_legacy_backup_count)
    if (env_legacy_logfile_size := os.environ.get("BACKEND_LOG_FILE_SIZE", None)) is not None:
        legacy_logfile_size = f"{env_legacy_logfile_size}M"
        config.file.rotation_size = ByteSize(legacy_logfile_size)

    fmt = "%(timestamp) %(level) %(name) %(processName) %(message)"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.file.path / config.file.filename,
        backupCount=config.file.backup_count,
        maxBytes=config.file.rotation_size,
        encoding="utf-8",
    )
    file_handler.setLevel(config.level)
    file_handler.setFormatter(CustomJsonFormatter(fmt))
    yield file_handler


@contextlib.contextmanager
def setup_logstash_handler(config: LoggingConfig) -> Iterator[logging.Handler]:
    if config.logstash is None:
        raise ConfigurationError(
            "logging.setup_logstash_log_handler: "
            "The 'logstash' logging driver is active but its config is missing"
        )

    from .handler.logstash import LogstashHandler

    drv_config = config.logstash
    logstash_handler = LogstashHandler(
        endpoint=(drv_config.endpoint.host, drv_config.endpoint.port),
        protocol=drv_config.protocol,
        ssl_enabled=drv_config.ssl_enabled,
        ssl_verify=drv_config.ssl_verify,
        myhost="hostname",  # TODO: implement
    )
    logstash_handler.setLevel(config.level)
    logstash_handler.setFormatter(SerializedExceptionFormatter())
    yield logstash_handler
    logstash_handler.cleanup()


@contextlib.contextmanager
def setup_graylog_handler(config: LoggingConfig) -> Iterator[logging.Handler]:
    if config.graylog is None:
        raise ConfigurationError(
            "logging.setup_graylog_log_handler: "
            "The 'graylog' logging driver is active but its config is missing"
        )

    from .handler.graylog import setup_graylog_handler as setup_impl

    graylog_handler = setup_impl(config)
    graylog_handler.setFormatter(SerializedExceptionFormatter())
    yield graylog_handler
    graylog_handler.close()


def log_processor(
    config: LoggingConfig,
    parent_pid: int,
    log_endpoint: str,
    ready_event: threading.Event,
    msgpack_options: MsgpackOptions,
) -> None:
    """
    A thread function that runs in the parent process to invoke log handlers configured from the drivers.
    """
    # For future references: when implementing new kind of logging adapters,
    # make sure to adapt our custom `Formatter.formatException()` approach;
    # Otherwise it won't print out EXCEPTION level log (along with the traceback).
    with contextlib.ExitStack() as handler_stack:
        console_handler = None
        if "console" in config.drivers:
            console_handler = handler_stack.enter_context(setup_console_log_handler(config))
        external_handlers: list[logging.Handler] = []
        if "file" in config.drivers:
            external_handlers.append(handler_stack.enter_context(setup_file_log_handler(config)))
        if "logstash" in config.drivers:
            external_handlers.append(handler_stack.enter_context(setup_logstash_handler(config)))
        if "graylog" in config.drivers:
            external_handlers.append(handler_stack.enter_context(setup_graylog_handler(config)))

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
                    for handler in external_handlers:
                        handler.emit(rec)
                except OSError:
                    # don't terminate the log worker.
                    continue
        finally:
            agg_sock.close()
            zctx.term()
