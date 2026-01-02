from __future__ import annotations

from typing import Optional

from aiohttp import ClientTimeout
from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema


class HttpTimeoutConfig(BaseConfigSchema):
    """
    Timeout configuration for a single HTTP request.
    Default values follow aiohttp defaults: total=300s, sock_connect=30s.
    """

    total: Optional[float] = Field(
        default=300.0,
        description="""
        Total timeout for the entire request (in seconds).
        None means no timeout.
        """,
        examples=[300.0],
    )
    connect: Optional[float] = Field(
        default=None,
        description="""
        Timeout for acquiring a connection from the pool (in seconds).
        None means no timeout.
        """,
        examples=[60.0],
    )
    sock_connect: Optional[float] = Field(
        default=30.0,
        description="""
        Timeout for connecting to a peer for a new connection (in seconds).
        None means no timeout.
        """,
        examples=[30.0],
        validation_alias=AliasChoices("sock-connect", "sock_connect"),
        serialization_alias="sock-connect",
    )
    sock_read: Optional[float] = Field(
        default=None,
        description="""
        Timeout for reading a portion of data from a peer (in seconds).
        None means no timeout.
        """,
        examples=[300.0],
        validation_alias=AliasChoices("sock-read", "sock_read"),
        serialization_alias="sock-read",
    )

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
