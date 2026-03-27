from __future__ import annotations

from typing import Annotated

from aiohttp import ClientTimeout
from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample


class HttpTimeoutConfig(BaseConfigSchema):
    """
    Timeout configuration for a single HTTP request.
    Default values follow aiohttp defaults: total=300s, sock_connect=30s.
    """

    total: Annotated[
        float | None,
        Field(default=300.0),
        BackendAIConfigMeta(
            description=(
                "Total timeout for the entire request (in seconds). None means no timeout."
            ),
            added_version="25.18.0",
            example=ConfigExample(local="300.0", prod="300.0"),
        ),
    ]
    connect: Annotated[
        float | None,
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Timeout for acquiring a connection from the pool (in seconds). "
                "None means no timeout."
            ),
            added_version="25.18.0",
            example=ConfigExample(local="60.0", prod="60.0"),
        ),
    ]
    sock_connect: Annotated[
        float | None,
        Field(
            default=30.0,
            validation_alias=AliasChoices("sock-connect", "sock_connect"),
            serialization_alias="sock-connect",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for connecting to a peer for a new connection (in seconds). "
                "None means no timeout."
            ),
            added_version="25.18.0",
            example=ConfigExample(local="30.0", prod="30.0"),
        ),
    ]
    sock_read: Annotated[
        float | None,
        Field(
            default=None,
            validation_alias=AliasChoices("sock-read", "sock_read"),
            serialization_alias="sock-read",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout for reading a portion of data from a peer (in seconds). "
                "None means no timeout."
            ),
            added_version="25.18.0",
            example=ConfigExample(local="300.0", prod="300.0"),
        ),
    ]

    def to_client_timeout(self) -> ClientTimeout:
        """
        Convert timeout config to aiohttp ClientTimeout instance.
        """
        return ClientTimeout(
            total=self.total,
            connect=self.connect,
            sock_connect=self.sock_connect,
            sock_read=self.sock_read,
        )
