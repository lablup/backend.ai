import logging
import os
import threading
import time
from pathlib import Path

import trafaret as t

from ai.backend.common.msgpack import DEFAULT_PACK_OPTS, DEFAULT_UNPACK_OPTS
from ai.backend.logging import BraceStyleAdapter, LocalLogger, Logger
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.logger import MsgpackOptions
from ai.backend.logging.types import LogLevel

test_log_config = LoggingConfig(
    level=LogLevel.DEBUG,
    pkg_ns={"": LogLevel.DEBUG},
    drivers=[LogDriver.CONSOLE],
    console=ConsoleConfig(
        colored=True,
    ),
)

test_log_path = Path(f"/tmp/bai-testing-agent-logger-{os.getpid()}.sock")
msgpack_opts: MsgpackOptions = {
    "pack_opts": DEFAULT_PACK_OPTS,
    "unpack_opts": DEFAULT_UNPACK_OPTS,
}

log = BraceStyleAdapter(logging.getLogger("ai.backend.common.testing"))


class NotPicklableClass:
    """A class that cannot be pickled."""

    def __reduce__(self):
        raise TypeError("this is not picklable")


class NotUnpicklableClass:
    """A class that is pickled successfully but cannot be unpickled."""

    def __init__(self, x):
        if x == 1:
            raise TypeError("this is not unpicklable")

    def __reduce__(self):
        return type(self), (1,)


def get_logger_thread() -> threading.Thread | None:
    for thread in threading.enumerate():
        if thread.name == "Logger":
            return thread
    return None


def test_logger(unused_tcp_port, capsys):
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{test_log_path}"
    logger = Logger(
        test_log_config,
        is_master=True,
        log_endpoint=log_endpoint,
        msgpack_options=msgpack_opts,
    )
    with logger:
        assert test_log_path.exists()
        log.warning("blizzard warning {}", 123)
        assert get_logger_thread() is not None
    assert not test_log_path.exists()
    assert get_logger_thread() is None
    captured = capsys.readouterr()
    assert "blizzard warning 123" in captured.err


def test_local_logger(capsys):
    logger = LocalLogger(test_log_config)
    with logger:
        log.warning("blizzard warning {}", 456)
        assert get_logger_thread() is None
    assert get_logger_thread() is None
    captured = capsys.readouterr()
    assert "blizzard warning 456" in captured.err


def test_logger_not_picklable(capsys):
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{test_log_path}"
    logger = Logger(
        test_log_config,
        is_master=True,
        log_endpoint=log_endpoint,
        msgpack_options=msgpack_opts,
    )
    with logger:
        log.warning("blizzard warning {}", NotPicklableClass())
    assert not test_log_path.exists()
    assert get_logger_thread() is None
    captured = capsys.readouterr()
    assert "blizzard warning" in captured.err
    assert "NotPicklableClass" in captured.err


def test_logger_trafaret_dataerror(capsys):
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{test_log_path}"
    logger = Logger(
        test_log_config,
        is_master=True,
        log_endpoint=log_endpoint,
        msgpack_options=msgpack_opts,
    )
    with logger:
        try:
            iv = t.Int()
            iv.check("x")
        except t.DataError:
            log.exception("simulated dataerror")
    assert not test_log_path.exists()
    assert get_logger_thread() is None
    captured = capsys.readouterr()
    assert "simulated dataerror" in captured.err
    assert "Traceback (most recent call last)" in captured.err
    assert "value can't be converted to int" in captured.err


def test_logger_not_unpicklable(capsys):
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f"ipc://{test_log_path}"
    logger = Logger(
        test_log_config,
        is_master=True,
        log_endpoint=log_endpoint,
        msgpack_options=msgpack_opts,
    )
    with logger:
        log.warning("blizzard warning {}", NotUnpicklableClass(0))
        time.sleep(1.0)
        assert get_logger_thread() is not None, "logger thread must be alive"
    assert not test_log_path.exists()
    assert get_logger_thread() is None
    captured = capsys.readouterr()
    assert "blizzard warning" in captured.err
    assert "NotUnpicklableClass" in captured.err
