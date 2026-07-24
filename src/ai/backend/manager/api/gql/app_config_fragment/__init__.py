"""GraphQL app config fragment module."""

from .resolver import (
    admin_app_config_fragments,
    app_config_fragment,
)
from .types import (
    AppConfigFragmentConnection,
    AppConfigFragmentEdge,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigScopeTypeFilterGQL,
)

__all__ = (
    # Types
    "AppConfigFragmentConnection",
    "AppConfigFragmentEdge",
    "AppConfigFragmentFilterGQL",
    "AppConfigFragmentGQL",
    "AppConfigFragmentOrderByGQL",
    "AppConfigFragmentOrderFieldGQL",
    "AppConfigScopeTypeFilterGQL",
    # Query resolvers
    "admin_app_config_fragments",
    "app_config_fragment",
)
