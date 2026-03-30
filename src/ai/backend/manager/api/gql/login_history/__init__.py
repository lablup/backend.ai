"""LoginHistory GraphQL API package."""

from .resolver import admin_login_history_v2, my_login_history_v2

__all__ = [
    "admin_login_history_v2",
    "my_login_history_v2",
]
