from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.user import UserID

__all__ = ("AppConfigScopeIdentifier",)


# Who an app config fragment belongs to, paired with its ``AppConfigScopeType``: a domain,
# a user, or nobody for ``public``.
type AppConfigScopeIdentifier = DomainID | UserID | None
