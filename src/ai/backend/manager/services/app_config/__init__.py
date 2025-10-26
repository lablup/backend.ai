"""App configuration service."""

from .processors import AppConfigProcessors
from .service import AppConfigService

__all__ = [
    "AppConfigService",
    "AppConfigProcessors",
]
