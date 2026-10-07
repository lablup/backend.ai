"""Manager-side request bodies for the AppProxy coordinator API.

Shared tag models (``SessionTagsModel`` / ``EndpointTagsModel`` / ``TagsModel``)
live in :mod:`ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types` —
import them from there instead of this module.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import TagsModel


class CreateEndpointRequestBody(BaseRequestModel):
    """Request body for the legacy single-endpoint AppProxy create API.

    Kept for paths that still call ``POST /v2/endpoints/{endpoint_id}``
    one deployment at a time. New code should prefer the bulk API
    (``BulkCreateEndpointRequest``) so circuit propagation to workers
    is batched per coordinator call.
    """

    version: str = Field(
        default="v2",
        description="Creation API version — always ``v2`` for this body.",
    )
    service_name: str = Field(
        ...,
        description=(
            "Human-readable service / endpoint name. Used when selecting "
            "a subdomain or building router names on the coordinator side."
        ),
    )
    tags: TagsModel = Field(
        ...,
        description="Session + endpoint metadata tags attached to the endpoint.",
    )
    open_to_public: bool = Field(
        default=False,
        description=(
            "If ``True``, AppProxy requires a valid API token on every "
            "incoming request and does not expose the endpoint publicly "
            "without authentication."
        ),
    )
    health_check: ModelHealthCheck | None = Field(
        default=None,
        description=(
            "Optional health check configuration. When present, the "
            "coordinator configures the load balancer to probe model "
            "service replicas using this path / interval / timeout."
        ),
    )


class SessionAppSessionInfo(BaseRequestModel):
    """Session identity sent with ``POST /v2/conf``."""

    id: UUID = Field(..., description="Session ID.")
    user_uuid: UUID = Field(..., description="Session owner's user ID.")
    group_id: UUID = Field(..., description="Session's project ID (legacy wire key).")
    access_key: str | None = Field(..., description="Session owner's access key.")
    domain_name: str = Field(..., description="Session's domain name.")


class CreateSessionAppTokenRequestBody(BaseRequestModel):
    """Request body for ``POST /v2/conf``, which issues a token for an interactive session app."""

    login_session_token: str | None = Field(..., description="Webserver login session token.")
    kernel_host: str = Field(..., description="Host the app port is reachable on.")
    kernel_port: int = Field(..., description="Host port of the app.")
    session: SessionAppSessionInfo = Field(..., description="Session identity.")
