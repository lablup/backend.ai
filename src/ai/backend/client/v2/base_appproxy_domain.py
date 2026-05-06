from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_client import BackendAIAppProxyClient


class BaseAppProxyDomainClient:
    _client: BackendAIAppProxyClient

    def __init__(self, client: BackendAIAppProxyClient) -> None:
        self._client = client
