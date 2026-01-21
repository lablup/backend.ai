from __future__ import annotations

from dataclasses import dataclass

import yarl


@dataclass(frozen=True)
class StorageProxyClientFacingInfo:
    """
    Dataclass containing endpoint information for client-facing storage proxy operations.
    This class provides endpoint URLs and configuration that can be sent to users.
    """

    base_url: yarl.URL
