from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def storage_manager_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..models.storage import StorageSessionManager

    root_ctx.storage_manager = StorageSessionManager(root_ctx.config_provider.config.volumes)
    yield
