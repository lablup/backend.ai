from __future__ import annotations

import logging
import sys
import traceback
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, override

from ai.backend.common.events.event_types.agent.anycast import AgentErrorEvent
from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.plugin.event import AbstractEventDispatcherPlugin
from ai.backend.common.plugin.monitor import AbstractErrorReporterPlugin
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter, LogLevel
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.error_log.creators import ErrorLogCreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.repositories.error_log import ErrorLogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ErrorMonitor(AbstractErrorReporterPlugin):
    _error_log_repository: ErrorLogRepository

    async def init(self, context: Any | None = None) -> None:
        if context is None:
            log.warning(
                "manager.plugin.error_monitor is initialized without the root context. "
                "The plugin is disabled.",
            )
            self.enabled = False
            return
        self.enabled = True
        root_ctx: RootContext = context["_root.context"]  # type: ignore
        self._error_log_repository = root_ctx.repositories.error_log.repository

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    async def capture_message(self, message: str) -> None:
        pass

    async def capture_exception(
        self,
        exc_instance: Exception | None = None,
        context: Mapping[str, Any] | None = None,
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
            severity = LogLevel.ERROR
        else:
            severity = context["severity"]
        if context is None or "user" not in context:
            user = None
        else:
            user = context["user"]
        message = "".join(traceback.format_exception_only(exc_type, exc_instance)).strip()

        error_log_severity = ErrorLogSeverity(severity.value.lower())
        creator = Creator(
            spec=ErrorLogCreatorSpec(
                severity=error_log_severity,
                source="manager",
                user=user,
                message=message,
                context_lang="python",
                context_env=dict(context) if context else {},
                traceback="".join(traceback.format_tb(tb)).strip(),
            )
        )
        await self._error_log_repository.create(creator)
        log.debug(
            'collected an error log [{}] "{}" from manager',
            severity.name,
            message,
        )


class ErrorEventDispatcher(AbstractEventDispatcherPlugin):
    _error_log_repository: ErrorLogRepository

    async def init(self, context: Any | None = None) -> None:
        if context is None:
            log.warning(
                "manager.plugin.error_event_dispatcher is initialized without the root context. "
                "The plugin is disabled.",
            )
            self.enabled = False
            return
        self.enabled = True
        root_ctx: RootContext = context
        self._error_log_repository = root_ctx.repositories.error_log.repository

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    @override
    async def handle_event(
        self,
        source: AgentId,
        event: AbstractEvent,
    ) -> None:
        if not isinstance(event, AgentErrorEvent):
            return
        if not self.enabled:
            return
        error_log_severity = ErrorLogSeverity(event.severity.value.lower())
        creator = Creator(
            spec=ErrorLogCreatorSpec(
                severity=error_log_severity,
                source=source,
                user=event.user,
                message=event.message,
                context_lang="python",
                context_env=dict(event.context_env) if event.context_env else {},
                traceback=event.traceback,
            )
        )
        await self._error_log_repository.create(creator)
        log.debug(
            'collected an error log [{}] "{}" from agent:{}',
            event.severity.name,
            event.message,
            source,
        )
