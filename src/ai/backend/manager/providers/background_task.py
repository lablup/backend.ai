from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager

if TYPE_CHECKING:
    from ..api.context import RootContext


class background_task_ctx:
    def __init__(self, root_ctx: RootContext) -> None:
        self.root_ctx = root_ctx

    async def __aenter__(self) -> None:
        self.root_ctx.background_task_manager = BackgroundTaskManager(
            self.root_ctx.event_producer,
            valkey_client=self.root_ctx.valkey_bgtask,
            server_id=self.root_ctx.config_provider.config.manager.id,
            bgtask_observer=self.root_ctx.metrics.bgtask,
        )

    async def __aexit__(self, *exc_info) -> None:
        pass

    async def shutdown(self) -> None:
        if hasattr(self.root_ctx, "background_task_manager"):
            await self.root_ctx.background_task_manager.shutdown()
