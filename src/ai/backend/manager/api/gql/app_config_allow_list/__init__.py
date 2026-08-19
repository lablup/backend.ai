"""GraphQL app config allow-list module."""

from .resolver import (
    admin_app_config_allow_list,
    admin_app_config_allow_lists,
    admin_create_app_config_allow_list,
    admin_purge_app_config_allow_list,
    admin_update_app_config_allow_list,
)
from .types import (
    AppConfigAllowListConnection,
    AppConfigAllowListEdge,
    AppConfigAllowListFilterGQL,
    AppConfigAllowListGQL,
    AppConfigAllowListOrderByGQL,
    AppConfigAllowListOrderFieldGQL,
    AppConfigScopeTypeFilterGQL,
    CreateAppConfigAllowListInputGQL,
    CreateAppConfigAllowListPayloadGQL,
    PurgeAppConfigAllowListPayloadGQL,
)

__all__ = (
    # Types
    "AppConfigAllowListConnection",
    "AppConfigAllowListEdge",
    "AppConfigAllowListFilterGQL",
    "AppConfigAllowListGQL",
    "AppConfigAllowListOrderByGQL",
    "AppConfigAllowListOrderFieldGQL",
    "AppConfigScopeTypeFilterGQL",
    "CreateAppConfigAllowListInputGQL",
    "CreateAppConfigAllowListPayloadGQL",
    "PurgeAppConfigAllowListPayloadGQL",
    # Query resolvers
    "admin_app_config_allow_list",
    "admin_app_config_allow_lists",
    # Mutation resolvers
    "admin_create_app_config_allow_list",
    "admin_purge_app_config_allow_list",
    "admin_update_app_config_allow_list",
)
