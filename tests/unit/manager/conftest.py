from __future__ import annotations

import logging
import os
import secrets
from collections.abc import Callable, Generator
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from ai.backend.common.lock import FileLock
from ai.backend.logging import LocalLogger, LogLevel
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    postgres_container,
    redis_container,
)


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


here = Path(__file__).parent

log = logging.getLogger("tests.manager.conftest")


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--rescan-cr-backend-ai",
        action="store_true",
        default=False,
        help="Enable tests marked as rescan_cr_backend_ai",
    )


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "rescan_cr_backend_ai: mark test to run only when --rescan-cr-backend-ai is set",
    )


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    if not config.getoption("--rescan-cr-backend-ai"):
        skip_flag = pytest.mark.skip(reason="--rescan-cr-backend-ai not set")
        for item in items:
            if "rescan_cr_backend_ai" in item.keywords:
                item.add_marker(skip_flag)


@pytest.fixture(scope="session", autouse=True)
def test_id() -> str:
    return secrets.token_hex(12)


@pytest.fixture(scope="session", autouse=True)
def test_ns(test_id: str) -> str:
    ret = f"testing-ns-{test_id}"
    os.environ["BACKEND_NAMESPACE"] = ret
    return ret


@pytest.fixture(scope="session")
def test_db(test_id: str) -> str:
    return f"test_db_{test_id}"


@pytest.fixture(scope="session")
def logging_config() -> Generator[LoggingConfig, None, None]:
    config = LoggingConfig(
        version=1,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
        drivers=[LogDriver.CONSOLE],
        console=ConsoleConfig(
            colored=None,
            format=LogFormat.VERBOSE,
        ),
        file=None,
        logstash=None,
        graylog=None,
        level=LogLevel.DEBUG,
        pkg_ns={
            "": LogLevel.INFO,
            "ai.backend": LogLevel.DEBUG,
            "tests": LogLevel.DEBUG,
            "alembic": LogLevel.INFO,
            "aiotools": LogLevel.INFO,
            "aiohttp": LogLevel.INFO,
            "sqlalchemy": LogLevel.WARNING,
        },
    )
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def ipc_base_path(test_id: str) -> Path:
    ipc_base_path = Path.cwd() / f"tmp/backend.ai/manager-testing/ipc-{test_id}"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    return ipc_base_path


@pytest.fixture
def file_lock_factory(
    ipc_base_path: Path,
    request: pytest.FixtureRequest,
) -> Callable[[str], FileLock]:
    def _make_lock(lock_id: str) -> FileLock:
        lock_path = ipc_base_path / f"testing.{lock_id}.lock"
        lock = FileLock(lock_path, timeout=0)
        request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
        return lock

    return _make_lock
