"""GraphQL app config definition module."""

from .resolver import (
    admin_app_config_definition,
    admin_app_config_definitions,
    admin_create_app_config_definition,
    admin_purge_app_config_definition,
)
from .types import (
    AppConfigDefinitionConnection,
    AppConfigDefinitionEdge,
    AppConfigDefinitionFilterGQL,
    AppConfigDefinitionGQL,
    AppConfigDefinitionOrderByGQL,
    AppConfigDefinitionOrderFieldGQL,
    CreateAppConfigDefinitionInputGQL,
    CreateAppConfigDefinitionPayloadGQL,
    PurgeAppConfigDefinitionInputGQL,
    PurgeAppConfigDefinitionPayloadGQL,
)

__all__ = (
    # Types
    "AppConfigDefinitionConnection",
    "AppConfigDefinitionEdge",
    "AppConfigDefinitionFilterGQL",
    "AppConfigDefinitionGQL",
    "AppConfigDefinitionOrderByGQL",
    "AppConfigDefinitionOrderFieldGQL",
    "CreateAppConfigDefinitionInputGQL",
    "CreateAppConfigDefinitionPayloadGQL",
    "PurgeAppConfigDefinitionInputGQL",
    "PurgeAppConfigDefinitionPayloadGQL",
    # Query resolvers
    "admin_app_config_definition",
    "admin_app_config_definitions",
    # Mutation resolvers
    "admin_create_app_config_definition",
    "admin_purge_app_config_definition",
)
