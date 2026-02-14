from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_client import BackendAIClient


class BaseDomainClient:
    _client: BackendAIClient

    def __init__(self, client: BackendAIClient) -> None:
        self._client = client
