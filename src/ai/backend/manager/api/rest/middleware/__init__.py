"""Global middleware modules for the Manager REST API.

Re-exports commonly used middlewares so that ``server.py`` (and future
new-style modules) can import them from a single location.
"""

from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.middlewares.request_id import request_id_middleware

from .auth import build_auth_middleware
from .exception import build_exception_middleware

__all__ = (
    "build_api_metric_middleware",
    "build_auth_middleware",
    "build_exception_middleware",
    "request_id_middleware",
)
