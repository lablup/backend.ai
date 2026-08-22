"""Entity types of the fair share tables."""

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "DOMAIN_FAIR_SHARE_ENTITY_TYPE",
    "PROJECT_FAIR_SHARE_ENTITY_TYPE",
    "USER_FAIR_SHARE_ENTITY_TYPE",
)

DOMAIN_FAIR_SHARE_ENTITY_TYPE = EntityType("domain_fair_share")
PROJECT_FAIR_SHARE_ENTITY_TYPE = EntityType("project_fair_share")
USER_FAIR_SHARE_ENTITY_TYPE = EntityType("user_fair_share")
