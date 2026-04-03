from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field


class OpenIDProviderConfig(BaseModel):
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
    client_secret: str = Field(
        description="The OAuth2 client secret.",
    )
    group_mapping: Mapping[str, Any] = Field(
        default_factory=dict,
        description="Mapping of OpenID group IDs to Backend.AI domain/project settings.",
    )
    group_order: str = Field(
        default="",
        description="Comma-separated priority order of group IDs for mapping.",
    )


class OIDCPluginConfig(BaseModel):
    openid: OpenIDProviderConfig = Field(
        description="OpenID Connect provider configuration.",
    )
    secret: str = Field(
        description="Secret key used for signing JWT tokens.",
    )
    login_uri: str = Field(
        description="The login page URI to redirect users to.",
    )
