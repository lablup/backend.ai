from ai.backend.common.data.entity.types import EntityType

__all__ = ("AUTH_ENTITY_TYPE",)


# Raw string mirroring the RBAC-managed EntityType.AUTH value. It names the credential
# and login-session state that answers for no other entity.
AUTH_ENTITY_TYPE = EntityType("auth")
