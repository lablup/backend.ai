"""App-proxy client registry.

Provides ``AppProxyClientRegistry`` which lazy-loads domain clients that
target inference runtimes fronted by Backend.AI's app-proxy (vLLM, SGLang,
NIM, TGI in Messages API mode, etc.). Mirrors the
:class:`BackendAIClientRegistry` pattern but uses
:class:`BackendAIAppProxyClient` (token-based, deployment URL per request)
instead of :class:`BackendAIAuthClient` (HMAC-signed manager API).
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .base_client import BackendAIAppProxyClient
from .config import ClientConfig

if TYPE_CHECKING:
    from .deployment_chat import DeploymentChatClient


class AppProxyClientRegistry:
    """Registry of domain clients targeting deployment runtimes via app-proxy."""

    _client: BackendAIAppProxyClient

    def __init__(self, client: BackendAIAppProxyClient) -> None:
        self._client = client

    @classmethod
    async def create(cls, config: ClientConfig) -> AppProxyClientRegistry:
        client = BackendAIAppProxyClient(config)
        return cls(client)

    async def close(self) -> None:
        await self._client.close()

    @cached_property
    def deployment_chat(self) -> DeploymentChatClient:
        from .deployment_chat import DeploymentChatClient

        return DeploymentChatClient(self._client)
