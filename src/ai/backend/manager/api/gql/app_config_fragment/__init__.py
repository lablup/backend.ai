"""GraphQL app config fragment module."""

from .resolver import (
    admin_app_config_fragments,
    app_config_fragment,
    scoped_app_config_fragments,
)
from .types import (
    AppConfigFragmentConnection,
    AppConfigFragmentEdge,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigFragmentScopeGQL,
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
    "AppConfigFragmentScopeGQL",
    "AppConfigScopeTypeFilterGQL",
    # Query resolvers
    "admin_app_config_fragments",
    "app_config_fragment",
    "scoped_app_config_fragments",
)
