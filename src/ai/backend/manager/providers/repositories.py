from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def repositories_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..repositories.repositories import Repositories
    from ..repositories.types import RepositoryArgs

    repositories = Repositories.create(
        args=RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_live_client=root_ctx.valkey_live,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
        )
    )
    root_ctx.repositories = repositories
    yield
