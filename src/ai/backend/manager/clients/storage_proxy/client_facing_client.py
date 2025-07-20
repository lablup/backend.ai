from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageProxyClientFacingClient:
    """
    Dataclass containing endpoint information for client-facing storage proxy operations.
    This class provides endpoint URLs and configuration that can be sent to users.
    """

    base_url: str
