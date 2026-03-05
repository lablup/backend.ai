"""LoginSession GraphQL API package.

Added in 26.3.0. Provides login session management API including
session listing, revocation, and login security policy updates.
"""

from .resolver import (
    my_login_sessions,
    revoke_login_session,
    update_user_login_security_policy,
)
from .types import (
    LoginSecurityPolicyGQL,
    LoginSessionGQL,
    RevokeLoginSessionPayloadGQL,
    UpdateLoginSecurityPolicyInputGQL,
    UpdateUserLoginSecurityPolicyPayloadGQL,
)

__all__ = [
    "LoginSessionGQL",
    "LoginSecurityPolicyGQL",
    "UpdateLoginSecurityPolicyInputGQL",
    "UpdateUserLoginSecurityPolicyPayloadGQL",
    "RevokeLoginSessionPayloadGQL",
    "my_login_sessions",
    "update_user_login_security_policy",
    "revoke_login_session",
]
