from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.web.config.unified import WebServerUnifiedConfig

from .redis import RedisProvider


@dataclass
class InfrastructureResources:
    """
    Resources provided by infrastructure dependencies.
    """

    redis: ValkeySessionClient


class InfrastructureComposer(DependencyComposer[WebServerUnifiedConfig, InfrastructureResources]):
    """
    Composer for infrastructure dependencies.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: WebServerUnifiedConfig,
    ) -> AsyncIterator[InfrastructureResources]:
        """
        Compose infrastructure dependencies.
        """
        redis = await stack.enter_dependency(RedisProvider(), setup_input)

        yield InfrastructureResources(redis=redis)
