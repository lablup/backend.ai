from __future__ import annotations

import logging
import sys
import traceback
from typing import TYPE_CHECKING, Any, Mapping

from ai.backend.common.events import AgentErrorEvent
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.monitor import AbstractErrorReporterPlugin
from ai.backend.common.types import AgentId, LogSeverity

from ..models import error_logs

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class ErrorMonitor(AbstractErrorReporterPlugin):
    async def init(self, context: Any = None) -> None:
        if context is None:
            log.warning(
                "manager.plugin.error_monitor is initialized without the root context. "
                "The plugin is disabled.",
            )
            self.enabled = False
            return
        else:
            self.enabled = True
        root_ctx: RootContext = context["_root.context"]  # type: ignore
        self.event_dispatcher = root_ctx.event_dispatcher
        self._evh = self.event_dispatcher.consume(AgentErrorEvent, None, self.handle_agent_error)
        self.db = root_ctx.db

    async def cleanup(self) -> None:
        if self.enabled:
            self.event_dispatcher.unconsume(self._evh)

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    async def capture_message(self, message: str) -> None:
        pass

    async def capture_exception(
        self,
        exc_instance: Exception = None,
        context: Mapping[str, Any] = None,
    ) -> None:
        if not self.enabled:
            return
        if exc_instance:
            tb = exc_instance.__traceback__
        else:
            _, sys_exc_instance, tb = sys.exc_info()
            if isinstance(sys_exc_instance, BaseException) and not isinstance(
                sys_exc_instance, Exception
            ):
                # bypass BaseException as they are used for controlling the process/coroutine lifecycles
                # instead of indicating actual errors
                return
            exc_instance = sys_exc_instance
        exc_type: Any = type(exc_instance)

        if context is None or "severity" not in context:
            severity = LogSeverity.ERROR
        else:
            severity = context["severity"]
        if context is None or "user" not in context:
            user = None
        else:
            user = context["user"]
        message = "".join(traceback.format_exception_only(exc_type, exc_instance)).strip()

        async with self.db.begin() as conn:
            query = error_logs.insert().values({
                "severity": severity.value.lower(),
                "source": "manager",
                "user": user,
                "message": message,
                "context_lang": "python",
                "context_env": context,
                "traceback": "".join(traceback.format_tb(tb)).strip(),
            })
            await conn.execute(query)
        log.debug(
            'collected an error log [{}] "{}" from manager',
            severity.name,
            message,
        )

    async def handle_agent_error(
        self,
        context: None,
        source: AgentId,
        event: AgentErrorEvent,
    ) -> None:
        if not self.enabled:
            return
        async with self.db.begin() as conn:
            query = error_logs.insert().values({
                "severity": event.severity.value.lower(),
                "source": source,
                "user": event.user,
                "message": event.message,
                "context_lang": "python",
                "context_env": event.context_env,
                "traceback": event.traceback,
            })
            await conn.execute(query)
        log.debug(
            'collected an error log [{}] "{}" from agent:{}',
            event.severity.name,
            event.message,
            source,
        )
