from pathlib import Path

from .abc import AbstractLogger
from .exceptions import ConfigurationError
from .logger import LocalLogger, Logger, NoopLogger, is_active
from .types import LogFormat, LogLevel
from .utils import BraceStyleAdapter

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()

__all__ = (
    "AbstractLogger",
    "BraceStyleAdapter",
    "ConfigurationError",
    "LocalLogger",
    "LogFormat",
    "LogLevel",
    "Logger",
    "NoopLogger",
    "is_active",
)
