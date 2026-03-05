"""LoginSession GraphQL node types."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import strawberry


@strawberry.type(
    name="LoginSessionGQL",
    description="Added in 26.3.0. Represents an active login session for a user.",
)
class LoginSessionGQL:
    """An active login session."""

    id: UUID = strawberry.field(description="Unique identifier of the login session.")
    session_token: str = strawberry.field(description="Opaque session token.")
    client_ip: str = strawberry.field(
        description="IP address of the client that created the session."
    )
    created_at: datetime = strawberry.field(description="Timestamp when the session was created.")
    expired_at: datetime | None = strawberry.field(
        description="Timestamp when the session expires, or None if no expiry."
    )
    reason: str | None = strawberry.field(
        description="Reason for session creation or revocation, if any."
    )


@strawberry.type(
    name="LoginSecurityPolicyGQL",
    description="Added in 26.3.0. Login security policy settings for a user.",
)
class LoginSecurityPolicyGQL:
    """Login security policy for a user."""

    max_concurrent_logins: int | None = strawberry.field(
        description="Maximum number of concurrent login sessions allowed. None means unlimited."
    )
