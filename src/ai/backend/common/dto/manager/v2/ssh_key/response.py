"""Response DTOs for SSH key DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

__all__ = ("SSHKeyNode",)


class SSHKeyNode(BaseResponseModel):
    """An SSH key of a user. The private key is never included."""

    id: SSHKeypairID = Field(description="The id of the SSH key.")
    field_id: UUID = Field(
        description=f"UUID of the SSH key. Added in {NEXT_RELEASE_VERSION}.",
    )
    user_id: UUID = Field(description="The id of the user the SSH key belongs to.")
    public_key: str = Field(description="The SSH public key.")
    is_default: bool = Field(description="Whether sessions use this SSH key.")
