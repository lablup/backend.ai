"""Manager-side request and response bodies for the AppProxy coordinator API.

Shared tag models (``SessionTagsModel`` / ``EndpointTagsModel`` / ``TagsModel``)
live in :mod:`ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types` —
import them from there instead of this module.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import TagsModel
from ai.backend.common.types import AccessKey


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


class AppTokenSessionIdentity(BaseRequestModel):
    """Session identity sent with ``POST /v2/conf``."""

    id: SessionID = Field(..., description="Session ID.")
    user_uuid: UserID = Field(..., description="Session owner's user ID.")
    group_id: ProjectID = Field(
        ...,
        description="Session's project ID. Coordinators predating 26.4 read only this key.",
    )
    access_key: AccessKey | None = Field(..., description="Session owner's access key.")
    domain_name: str = Field(..., description="Session's domain name.")


class CreateSessionAppTokenRequestBody(BaseRequestModel):
    """Request body for ``POST /v2/conf``, which issues a token for an interactive session app."""

    login_session_token: str | None = Field(..., description="Webserver login session token.")
    kernel_host: str = Field(..., description="Host the app port is reachable on.")
    kernel_port: int = Field(..., description="Host port of the app.")
    session: AppTokenSessionIdentity = Field(..., description="Session the token is issued for.")


class CreateSessionAppTokenResponseBody(BaseResponseModel):
    """Response body of ``POST /v2/conf``."""

    token: str = Field(..., description="Token to open the session app with.")
