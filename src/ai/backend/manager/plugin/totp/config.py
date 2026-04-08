from pydantic import BaseModel, Field

_DEFAULT_TOKEN_SECRET = "BACKEND_AI_TOKEN_SECRET"


class TOTPConfig(BaseModel):
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
        default=_DEFAULT_TOKEN_SECRET,
        description=("Secret used when creating TOTP registration token for anonymous users."),
    )
    token_lifetime: int = Field(
        default=300,
        description=("Lifetime for TOTP registration token in seconds. Default is 5 minutes."),
    )
