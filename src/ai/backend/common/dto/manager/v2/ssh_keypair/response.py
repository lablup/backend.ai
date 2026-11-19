"""Response DTOs for SSH keypair DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

__all__ = ("SSHKeypairNode",)


class SSHKeypairNode(BaseResponseModel):
    """An SSH keypair of a user. The private key is never included."""

    id: SSHKeypairID = Field(description="The id of the SSH keypair.")
    field_id: UUID = Field(
        description=f"UUID of the SSH keypair. Added in {NEXT_RELEASE_VERSION}.",
    )
    user_id: UUID = Field(description="The id of the user the SSH keypair belongs to.")
    public_key: str = Field(description="The SSH public key.")
    is_default: bool = Field(description="Whether sessions use this SSH keypair.")
