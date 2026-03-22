"""
Response DTOs for keypair DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "IssueMyKeypairPayload",
    "RevokeMyKeypairPayload",
    "SwitchMyMainAccessKeyPayload",
    "UpdateMyKeypairPayload",
)


class IssueMyKeypairPayload(BaseResponseModel):
    """Payload returned after issuing a new keypair."""

    access_key: str = Field(description="The newly generated access key.")
    secret_key: str = Field(
        description="The newly generated secret key. This value is only returned at creation time."
    )
    ssh_public_key: str = Field(description="The generated SSH public key.")


class RevokeMyKeypairPayload(BaseResponseModel):
    """Payload returned after revoking a keypair."""

    success: bool = Field(description="Whether the revocation was successful.")


class UpdateMyKeypairPayload(BaseResponseModel):
    """Payload returned after updating a keypair."""

    success: bool = Field(description="Whether the update was successful.")


class SwitchMyMainAccessKeyPayload(BaseResponseModel):
    """Payload returned after switching the main access key."""

    success: bool = Field(description="Whether the switch was successful.")
