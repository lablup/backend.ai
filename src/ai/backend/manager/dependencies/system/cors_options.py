from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiohttp_cors

from ai.backend.manager.api.types import CORSOptions

from .base import SystemDependency


class CORSOptionsDependency(SystemDependency[CORSOptions]):
    """Provides CORS options configuration."""

    @property
    def stage_name(self) -> str:
        return "cors-options"

    @asynccontextmanager
    async def provide(self, setup_input: object) -> AsyncIterator[CORSOptions]:
        yield {
            "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
                allow_credentials=False, expose_headers="*", allow_headers="*"
            ),
        }
