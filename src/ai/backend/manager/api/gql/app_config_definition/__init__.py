"""GraphQL app config definition module."""

from .resolver import (
    admin_create_app_config_definition,
    admin_purge_app_config_definition,
    app_config_definition,
    app_config_definitions,
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
    "PurgeAppConfigDefinitionPayloadGQL",
    # Query resolvers
    "app_config_definition",
    "app_config_definitions",
    # Mutation resolvers
    "admin_create_app_config_definition",
    "admin_purge_app_config_definition",
)
