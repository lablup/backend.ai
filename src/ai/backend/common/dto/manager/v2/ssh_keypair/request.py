"""Request DTOs for SSH keypair DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("UploadMySSHKeypairInput",)


class UploadMySSHKeypairInput(BaseRequestModel):
    """A public key the caller uploads to their own SSH keypairs."""

    public_key: str = Field(
        description=(
            "The SSH public key in the OpenSSH single-line format. It becomes the default "
            "only when the caller has no default yet."
        )
    )
