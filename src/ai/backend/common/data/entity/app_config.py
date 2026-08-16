from typing import NewType
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "APP_CONFIG_ALLOW_LIST_ENTITY_TYPE",
    "AppConfigScopeID",
)


# Raw string mirroring the RBAC-managed EntityType.APP_CONFIG_ALLOW_LIST value.
APP_CONFIG_ALLOW_LIST_ENTITY_TYPE = EntityType("app_config_allow_list")

# Who an app config fragment belongs to. Polymorphic across scope kinds (domain/user); the
# concrete kind is discriminated by the accompanying ``AppConfigScopeType``, and ``public``
# has no owner at all, so its absence is spelled ``| None`` at each use.
AppConfigScopeID = NewType("AppConfigScopeID", UUID)
