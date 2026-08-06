"""GraphQL app config fragment module."""

from .resolver import (
    admin_app_config_fragments,
    app_config_fragment,
    my_app_config_fragments_by_names,
    my_upsert_app_config_fragments,
    scoped_app_config_fragments_by_names,
    scoped_upsert_app_config_fragments,
)
from .types import (
    AppConfigFragmentConnection,
    AppConfigFragmentEdge,
    AppConfigFragmentFilterGQL,
    AppConfigFragmentGQL,
    AppConfigFragmentOrderByGQL,
    AppConfigFragmentOrderFieldGQL,
    AppConfigFragmentUpsertErrorGQL,
    AppConfigFragmentUpsertItemGQL,
    AppConfigScopeRefGQL,
    AppConfigScopeTypeFilterGQL,
    MyUpsertAppConfigFragmentsInputGQL,
    ScopedUpsertAppConfigFragmentsInputGQL,
    UpsertAppConfigFragmentsPayloadGQL,
)

__all__ = (
    # Types
    "AppConfigFragmentConnection",
    "AppConfigFragmentEdge",
    "AppConfigFragmentFilterGQL",
    "AppConfigFragmentGQL",
    "AppConfigFragmentOrderByGQL",
    "AppConfigFragmentOrderFieldGQL",
    "AppConfigScopeRefGQL",
    "AppConfigFragmentUpsertErrorGQL",
    "AppConfigFragmentUpsertItemGQL",
    "AppConfigScopeTypeFilterGQL",
    "MyUpsertAppConfigFragmentsInputGQL",
    "ScopedUpsertAppConfigFragmentsInputGQL",
    "UpsertAppConfigFragmentsPayloadGQL",
    # Query resolvers
    "admin_app_config_fragments",
    "app_config_fragment",
    "scoped_app_config_fragments_by_names",
    "my_app_config_fragments_by_names",
    # Mutation resolvers
    "my_upsert_app_config_fragments",
    "scoped_upsert_app_config_fragments",
)
