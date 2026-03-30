"""
Request DTOs for etcd DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "DeleteConfigInput",
    "GetConfigInput",
    "GetResourceMetadataInput",
    "SetConfigInput",
)


class GetConfigInput(BaseRequestModel):
    """Input for reading an etcd configuration key."""

    key: str = Field(min_length=1, description="etcd key to read.")
    prefix: bool = Field(
        default=False,
        description="If true, read all keys sharing the given prefix.",
    )

    @field_validator("key")
    @classmethod
    def key_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("key must not be blank or whitespace-only")
        return stripped


class SetConfigInput(BaseRequestModel):
    """Input for writing an etcd configuration key."""

    key: str = Field(min_length=1, description="etcd key to write.")
    value: Any = Field(description="Value to store (scalar or nested mapping).")

    @field_validator("key")
    @classmethod
    def key_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("key must not be blank or whitespace-only")
        return stripped


class DeleteConfigInput(BaseRequestModel):
    """Input for deleting an etcd configuration key."""

    key: str = Field(min_length=1, description="etcd key to delete.")
    prefix: bool = Field(
        default=False,
        description="If true, delete all keys sharing the given prefix.",
    )

    @field_validator("key")
    @classmethod
    def key_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("key must not be blank or whitespace-only")
        return stripped


class GetResourceMetadataInput(BaseRequestModel):
    """Input for querying resource slot metadata."""

    sgroup: str | None = Field(
        default=None,
        description="Scaling group name to filter resource metadata by.",
    )
