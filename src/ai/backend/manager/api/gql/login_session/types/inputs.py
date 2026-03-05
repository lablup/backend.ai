"""LoginSession GraphQL input types."""

from __future__ import annotations

import strawberry


@strawberry.input(
    name="UpdateLoginSecurityPolicyInput",
    description=(
        "Added in 26.3.0. Input for updating a user's login security policy. "
        "max_concurrent_logins must be a positive integer or None (unlimited)."
    ),
)
class UpdateLoginSecurityPolicyInputGQL:
    """Input for updating login security policy."""

    max_concurrent_logins: int | None = strawberry.field(
        default=None,
        description=(
            "Maximum number of concurrent login sessions allowed. "
            "Must be a positive integer (greater than 0), or None for unlimited. "
            "Zero and negative values are rejected."
        ),
    )

    def __post_init__(self) -> None:
        if self.max_concurrent_logins is not None and self.max_concurrent_logins <= 0:
            raise ValueError("max_concurrent_logins must be a positive integer or None")
