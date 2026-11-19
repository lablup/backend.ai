"""Response DTOs for SSH keypair DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID

__all__ = (
    "UploadMySSHKeypairPayload",
    "SSHKeypairNode",
    "SwitchDefaultSSHKeypairPayload",
)


class SSHKeypairNode(BaseResponseModel):
    """An SSH keypair of a user. The private key is never included."""

    id: SSHKeypairID = Field(description="The id of the SSH keypair.")
    user_id: UUID = Field(description="The id of the user the SSH keypair belongs to.")
    public_key: str = Field(description="The SSH public key.")
    is_default: bool = Field(description="Whether sessions use this SSH keypair.")


class UploadMySSHKeypairPayload(BaseResponseModel):
    """The SSH keypair the upload made."""

    ssh_keypair: SSHKeypairNode = Field(description="The uploaded SSH keypair.")


class SwitchDefaultSSHKeypairPayload(BaseResponseModel):
    """The SSH keypair that became the default."""

    ssh_keypair: SSHKeypairNode = Field(description="The new default SSH keypair.")
