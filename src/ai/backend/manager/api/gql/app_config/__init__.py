"""AppConfig (merged view) GraphQL API package."""

from .resolver import (
    admin_app_configs,
    public_app_config_fragments,
    scoped_app_configs,
)
from .types import (
    AppConfigConnectionGQL,
    AppConfigFilterGQL,
    AppConfigGQL,
    AppConfigOrderByGQL,
    AppConfigOrderFieldGQL,
    AppConfigScopeGQL,
)

__all__ = [
    # Queries
    "scoped_app_configs",
    "admin_app_configs",
    "public_app_config_fragments",
    # Types
    "AppConfigGQL",
    "AppConfigConnectionGQL",
    "AppConfigFilterGQL",
    "AppConfigOrderByGQL",
    "AppConfigOrderFieldGQL",
    "AppConfigScopeGQL",
]
