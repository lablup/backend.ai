"""Request DTOs for SSH key DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("MyUploadSSHKeyInput",)


class MyUploadSSHKeyInput(BaseRequestModel):
    """A public key the caller uploads to their own SSH keys."""

    public_key: str = Field(
        min_length=1,
        # The longest key ssh-keygen makes (RSA 16384) is 2772 characters before its comment.
        max_length=3000,
        description=(
            "The SSH public key in the OpenSSH single-line format. It becomes the default "
            "only when the caller has no default yet."
        ),
    )
