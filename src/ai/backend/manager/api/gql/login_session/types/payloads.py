"""LoginSession GraphQL mutation payload types."""

from __future__ import annotations

import strawberry

from .node import LoginSecurityPolicyGQL


@strawberry.type(
    name="UpdateUserLoginSecurityPolicyPayload",
    description="Added in 26.3.0. Payload for updateUserLoginSecurityPolicy mutation.",
)
class UpdateUserLoginSecurityPolicyPayloadGQL:
    """Payload for login security policy update."""

    login_security_policy: LoginSecurityPolicyGQL = strawberry.field(
        description="The updated login security policy."
    )


@strawberry.type(
    name="RevokeLoginSessionPayload",
    description="Added in 26.3.0. Payload for revokeLoginSession mutation.",
)
class RevokeLoginSessionPayloadGQL:
    """Payload for login session revocation."""

    success: bool = strawberry.field(description="Whether the session was successfully revoked.")
