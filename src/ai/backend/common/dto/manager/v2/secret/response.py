"""
Response DTOs for secret DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminReencryptSecretsPayload",
    "AdminSecretStatusPayload",
    "SecretKeyCount",
)


class SecretKeyCount(BaseResponseModel):
    """How many stored secrets of one column one provider's one key holds."""

    column: str = Field(description="The encrypted column these secrets are stored in.")
    provider_type: str = Field(
        description="The key provider holding these secrets. 'plain' means legacy plaintext."
    )
    key_id: str | None = Field(
        default=None, description="The key within that provider. Unset for plaintext."
    )
    count: int = Field(description="How many stored secrets that key holds.")


class AdminSecretStatusPayload(BaseResponseModel):
    """Which key each stored secret sits on, across every encrypted column."""

    write_provider_type: str = Field(
        description="The key provider new and re-encrypted secrets are written through."
    )
    counts: list[SecretKeyCount] = Field(
        description="The stored secrets, grouped by column and by the key holding them."
    )


class AdminReencryptSecretsPayload(BaseResponseModel):
    """What one re-encryption pass wrote, and what the columns hold afterwards."""

    scanned: int = Field(description="How many rows this pass read.")
    reencrypted: int = Field(description="How many rows this pass wrote back.")
    status: AdminSecretStatusPayload = Field(
        description="The count per column and key id after this pass."
    )
