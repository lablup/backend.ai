from __future__ import annotations

import logging

from ai.backend.logging.config import default_pkg_ns
from ai.backend.logging.logger import LocalLogger
from ai.backend.logging.types import LogLevel


class TestLocalLoggerLogLevel:
    def test_log_level_applies_to_the_package_namespace(self) -> None:
        with LocalLogger(log_level=LogLevel.DEBUG):
            assert logging.getLogger("ai.backend.some.module").isEnabledFor(logging.DEBUG)

    def test_log_level_does_not_change_the_defaults(self) -> None:
        with LocalLogger(log_level=LogLevel.DEBUG):
            pass
        assert default_pkg_ns["ai.backend"] == LogLevel.INFO
