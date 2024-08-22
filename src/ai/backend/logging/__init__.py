from pathlib import Path

from .abc import AbstractLogger
from .exceptions import ConfigurationError
from .logger import LocalLogger, Logger, NoopLogger, is_active
from .utils import BraceStyleAdapter

__version__ = (Path(__file__).parent / "VERSION").read_text().strip()

__all__ = (
    "AbstractLogger",
    "Logger",
    "LocalLogger",
    "NoopLogger",
    "BraceStyleAdapter",
    "is_active",
    "ConfigurationError",
)
