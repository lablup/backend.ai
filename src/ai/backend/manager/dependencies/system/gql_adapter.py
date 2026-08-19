from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.api.gql.adapter import BaseGQLAdapter

from .base import SystemDependency


class GQLAdapterDependency(SystemDependency[BaseGQLAdapter]):
    """Provides BaseGQLAdapter instance."""

    @property
    @override
    def stage_name(self) -> str:
        return "gql-adapter"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: object) -> AsyncIterator[BaseGQLAdapter]:
        yield BaseGQLAdapter()
