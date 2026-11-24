"""Request DTOs for SSH key DTO v2."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "MySearchSSHKeysInput",
    "MyUploadSSHKeyInput",
    "SSHKeyFilter",
    "SSHKeyOrder",
    "SSHKeyOrderField",
    "ScopedSearchSSHKeysInput",
)


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


class SSHKeyFilter(BaseRequestModel):
    """Filter for SSH keys."""

    is_default: bool | None = Field(
        default=None, description="Filter by whether sessions use the SSH key."
    )


class SSHKeyOrderField(StrEnum):
    """Fields available for ordering SSH keys."""

    IS_DEFAULT = "is_default"


class SSHKeyOrder(BaseRequestModel):
    """Order specification for SSH keys."""

    field: SSHKeyOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchSSHKeysInput(BaseRequestModel):
    """Search the SSH keys of one user."""

    user_id: UUID = Field(description="The user whose SSH keys are read.")
    filter: SSHKeyFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SSHKeyOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class MySearchSSHKeysInput(BaseRequestModel):
    """Search the caller's own SSH keys."""

    filter: SSHKeyFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SSHKeyOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
