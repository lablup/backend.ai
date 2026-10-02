from collections.abc import Mapping
from typing import Any, Self

from pydantic import Field, model_validator

from ai.backend.common.types import BackendAISchema


class OpenIDProviderConfig(BackendAISchema):
    well_known: str | None = Field(
        default=None,
        description=(
            "The OpenID Connect well-known configuration URL. "
            "If provided, authorization_endpoint, token_endpoint, and jwks_uri "
            "are fetched automatically."
        ),
    )
    authorization_endpoint: str | None = Field(
        default=None,
        description="The authorization endpoint URL. Required if well_known is not set.",
    )
    token_endpoint: str | None = Field(
        default=None,
        description="The token endpoint URL. Required if well_known is not set.",
    )
    jwks_uri: str | None = Field(
        default=None,
        description="The JWKS URI for verifying tokens. Required if well_known is not set.",
    )
    client_id: str = Field(
        description="The OAuth2 client ID.",
    )
    client_secret: str | None = Field(
        default=None,
        description=(
            "The OAuth2 client secret. Set either this or private_key and certificate, not both."
        ),
    )
    private_key: str | None = Field(
        default=None,
        description=(
            "PEM-encoded RSA private key that signs the client assertion "
            "for private_key_jwt client authentication. Requires certificate."
        ),
    )
    certificate: str | None = Field(
        default=None,
        description=(
            "PEM-encoded certificate of private_key, registered with the provider. "
            "Its SHA-256 thumbprint is sent as the x5t#S256 assertion header."
        ),
    )
    client_assertion_alg: str = Field(
        default="PS256",
        description="The JWS algorithm that signs the client assertion.",
    )
    group_mapping: Mapping[str, Any] = Field(
        default_factory=dict,
        description="Mapping of OpenID group IDs to Backend.AI domain/project settings.",
    )
    group_order: str = Field(
        default="",
        description="Comma-separated priority order of group IDs for mapping.",
    )

    @model_validator(mode="after")
    def _validate_client_credential(self) -> Self:
        if (self.private_key is None) != (self.certificate is None):
            raise ValueError("private_key and certificate must be set together.")
        if (self.client_secret is None) == (self.private_key is None):
            raise ValueError("Set exactly one of client_secret or private_key and certificate.")
        return self


class OIDCHookConfig(BackendAISchema):
    secret: str = Field(
        description="Secret key used for signing and verifying JWT tokens.",
    )

    model_config = {"extra": "ignore"}


class OIDCWebAppConfig(BackendAISchema):
    openid: OpenIDProviderConfig = Field(
        description="OpenID Connect provider configuration.",
    )
    secret: str = Field(
        description="Secret key used for signing JWT tokens.",
    )
    login_uri: str = Field(
        description="The login page URI to redirect users to.",
    )
    allowed_redirect_hosts: list[str] | None = Field(
        default=None,
        description=(
            "Hostnames a sign-in may return to, in addition to the login_uri host. "
            "When set, a sign-in started from any other host returns to login_uri. "
            "When unset, any return address is accepted."
        ),
    )

    model_config = {"extra": "ignore"}
