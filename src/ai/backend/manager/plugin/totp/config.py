from pydantic import Field

from ai.backend.common.types import BackendAISchema


class TOTPConfig(BackendAISchema):
    issuer: str = Field(
        default="Backend.AI",
        description="Issuer name for TOTP.",
    )
    forced: bool = Field(
        default=False,
        description=(
            "Whether TOTP is forced for all users. If set to true, users must register TOTP."
        ),
    )
    totp_registration_url: str | None = Field(
        default=None,
        description=(
            "URL to register TOTP. "
            "If set, users who have not registered TOTP will be redirected to this URL for TOTP registration."
        ),
    )
    token_secret: str = Field(
        min_length=32,
        description=(
            "Secret used when creating TOTP registration token for anonymous users. "
            "Must contain at least 32 characters."
        ),
    )
    token_lifetime: int = Field(
        default=300,
        description=("Lifetime for TOTP registration token in seconds. Default is 5 minutes."),
    )
