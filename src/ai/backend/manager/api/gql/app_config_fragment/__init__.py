"""GraphQL app config fragment module."""

from .resolver import (
    admin_app_config_fragments,
    app_config_fragment,
    my_upsert_app_config_fragments,
    scoped_upsert_app_config_fragments,
)
from .types import (
    AppConfigFragmentConnection,
    AppConfigFragmentEdge,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigFragmentUpsertItemGQL,
    AppConfigScopeTypeFilterGQL,
    MyUpsertAppConfigFragmentsInputGQL,
    ScopedUpsertAppConfigFragmentsInputGQL,
)

__all__ = (
    # Types
    "AppConfigFragmentConnection",
    "AppConfigFragmentEdge",
    "AppConfigFragmentFilterGQL",
    "AppConfigFragmentGQL",
    "AppConfigFragmentOrderByGQL",
    "AppConfigFragmentOrderFieldGQL",
    "AppConfigFragmentUpsertItemGQL",
    "AppConfigScopeTypeFilterGQL",
    "MyUpsertAppConfigFragmentsInputGQL",
    "ScopedUpsertAppConfigFragmentsInputGQL",
    # Query resolvers
    "admin_app_config_fragments",
    "app_config_fragment",
    # Mutation resolvers
    "my_upsert_app_config_fragments",
    "scoped_upsert_app_config_fragments",
)
