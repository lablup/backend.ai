"""GraphQL app config fragment module."""

from .resolver import (
    admin_app_config_fragments,
    app_config_fragment,
    app_config_fragments_by_names,
    my_app_config_fragments_by_names,
    my_upsert_app_config_fragments,
    upsert_app_config_fragments,
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
    UpsertAppConfigFragmentsInputGQL,
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
    "UpsertAppConfigFragmentsInputGQL",
    # Query resolvers
    "admin_app_config_fragments",
    "app_config_fragment",
    "app_config_fragments_by_names",
    "my_app_config_fragments_by_names",
    # Mutation resolvers
    "my_upsert_app_config_fragments",
    "upsert_app_config_fragments",
)
