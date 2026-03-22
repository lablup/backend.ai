from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_client import BackendAIAuthClient


class BaseDomainClient:
    _client: BackendAIAuthClient

    def __init__(self, client: BackendAIAuthClient) -> None:
        self._client = client
