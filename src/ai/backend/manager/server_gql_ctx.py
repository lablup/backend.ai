from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api.context import RootContext


@asynccontextmanager
async def gql_adapters_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """
    Initialize GraphQL adapters.

    These adapters are created once at server startup and reused across all GraphQL requests.
    """
    from .api.gql.adapter import BaseGQLAdapter

    root_ctx.gql_adapter = BaseGQLAdapter()

    yield
