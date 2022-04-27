import logging
import os
from pathlib import Path
import threading
import time

from ai.backend.common.logging import Logger, BraceStyleAdapter


test_log_config = {
    'level': 'DEBUG',
    'drivers': ['console'],
    'pkg-ns': {'': 'DEBUG'},
    'console': {
        'colored': True,
    },
}

test_log_path = Path(f'/tmp/bai-testing-agent-logger-{os.getpid()}.sock')

log = BraceStyleAdapter(logging.getLogger('ai.backend.common.testing'))


def get_logger_thread():
    for t in threading.enumerate():
        if t.name == 'Logger':
            return t
    return None


def test_logger(unused_tcp_port):
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f'ipc://{test_log_path}'
    logger = Logger(test_log_config, is_master=True, log_endpoint=log_endpoint)
    with logger:
        assert test_log_path.exists()
        log.warning('blizzard warning {}', 123)
        assert get_logger_thread() is not None
    assert not test_log_path.exists()
    assert get_logger_thread() is None


class NotPicklableClass:
    """A class that cannot be pickled."""

    def __reduce__(self):
        raise TypeError('this is not picklable')


class NotUnpicklableClass:
    """A class that is pickled successfully but cannot be unpickled."""

    def __init__(self, x):
        if x == 1:
            raise TypeError('this is not unpicklable')

    def __reduce__(self):
        return type(self), (1, )


def test_logger_not_picklable():
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f'ipc://{test_log_path}'
    logger = Logger(test_log_config, is_master=True, log_endpoint=log_endpoint)
    with logger:
        # The following line should not throw an error.
        log.warning('blizzard warning {}', NotPicklableClass())
    assert not test_log_path.exists()
    assert get_logger_thread() is None


def test_logger_not_unpicklable():
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_endpoint = f'ipc://{test_log_path}'
    logger = Logger(test_log_config, is_master=True, log_endpoint=log_endpoint)
    with logger:
        log.warning('blizzard warning {}', NotUnpicklableClass(0))
        time.sleep(1.0)
        assert get_logger_thread() is not None, 'logger thread must be alive'
    assert not test_log_path.exists()
    assert get_logger_thread() is None
