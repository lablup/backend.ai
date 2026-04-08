"""
Response DTOs for keypair DTO v2.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "AdminCreateKeypairPayload",
    "AdminDeleteKeypairPayload",
    "AdminDeleteSSHKeypairPayload",
    "AdminGetSSHKeypairPayload",
    "AdminRegisterSSHKeypairPayload",
    "AdminSearchKeypairsPayload",
    "AdminUpdateKeypairPayload",
    "IssueMyKeypairPayload",
    "KeypairNode",
    "RevokeMyKeypairPayload",
    "SearchMyKeypairsPayload",
    "SSHKeypairNode",
    "SwitchMyMainAccessKeyPayload",
    "UpdateMyKeypairPayload",
)


class KeypairNode(BaseResponseModel):
    """Node DTO representing a keypair. Does not include secret_key or ssh_private_key."""

    id: str = Field(description="The primary key, equal to access_key. Used as the Relay Node ID.")
    access_key: str = Field(description="The access key (acts as the unique identifier).")
    is_active: bool | None = Field(default=None, description="Whether the keypair is active.")
    is_admin: bool | None = Field(
        default=None, description="Whether the keypair has admin privileges."
    )
    created_at: datetime | None = Field(default=None, description="When the keypair was created.")
    modified_at: datetime | None = Field(
        default=None, description="When the keypair was last modified."
    )
    last_used: datetime | None = Field(
        default=None, description="When the keypair was last used for an API call."
    )
    rate_limit: int = Field(description="API rate limit (requests per minute).")
    num_queries: int = Field(description="Total number of API queries made with this keypair.")
    resource_policy: str = Field(
        description="Name of the resource policy assigned to this keypair."
    )
    ssh_public_key: str | None = Field(
        default=None, description="The SSH public key associated with this keypair."
    )
    user_id: uuid.UUID = Field(description="UUID of the user who owns this keypair.")


class IssueMyKeypairPayload(BaseResponseModel):
    """Payload returned after issuing a new keypair."""

    keypair: KeypairNode = Field(description="The newly created keypair.")
    secret_key: str = Field(
        description="The newly generated secret key. This value is only returned at creation time."
    )


class RevokeMyKeypairPayload(BaseResponseModel):
    """Payload returned after revoking a keypair."""

    success: bool = Field(description="Whether the revocation was successful.")


class UpdateMyKeypairPayload(BaseResponseModel):
    """Payload returned after updating a keypair."""

    keypair: KeypairNode = Field(description="The updated keypair.")


class SwitchMyMainAccessKeyPayload(BaseResponseModel):
    """Payload returned after switching the main access key."""

    success: bool = Field(description="Whether the switch was successful.")


class SearchMyKeypairsPayload(BaseResponseModel):
    """Payload for keypair search responses."""

    items: list[KeypairNode] = Field(
        description="List of keypair entities matching the search criteria.",
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for the result set.",
    )


class AdminCreateKeypairPayload(BaseResponseModel):
    """Payload returned after admin creates a keypair for a user."""

    keypair: KeypairNode = Field(description="The newly created keypair.")
    secret_key: str = Field(description="The secret key. Only returned at creation time.")


class AdminUpdateKeypairPayload(BaseResponseModel):
    """Payload returned after admin updates a keypair."""

    keypair: KeypairNode = Field(description="The updated keypair.")


class AdminDeleteKeypairPayload(BaseResponseModel):
    """Payload returned after admin deletes a keypair."""

    access_key: str = Field(description="The access key of the deleted keypair.")


class AdminSearchKeypairsPayload(BaseResponseModel):
    """Payload for admin keypair search responses."""

    items: list[KeypairNode] = Field(
        description="List of keypair entities matching the search criteria.",
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for the result set.",
    )


class SSHKeypairNode(BaseResponseModel):
    """SSH keypair read model. Never includes the private key."""

    access_key: str = Field(description="Access key owning this SSH keypair.")
    ssh_public_key: str | None = Field(
        default=None, description="PEM-encoded SSH public key, or null if none is registered."
    )


class AdminRegisterSSHKeypairPayload(BaseResponseModel):
    """Payload returned after admin registers an SSH keypair for a user."""

    access_key: str = Field(description="Access key whose SSH keypair was updated.")


class AdminDeleteSSHKeypairPayload(BaseResponseModel):
    """Payload returned after admin clears a user's SSH keypair."""

    access_key: str = Field(description="Access key whose SSH keypair was cleared.")


class AdminGetSSHKeypairPayload(BaseResponseModel):
    """Payload returned by admin SSH keypair lookup (public key only)."""

    keypair: SSHKeypairNode = Field(description="SSH keypair public information.")
