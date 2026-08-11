"""GraphQL merged app config module."""

from .resolver import my_app_configs, public_app_configs
from .types import AppConfigGQL

__all__ = (
    # Types
    "AppConfigGQL",
    # Query resolvers
    "my_app_configs",
    "public_app_configs",
)
