from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.services.system_session_environ.actions.global_resolve import (
    GlobalResolveSystemSessionEnvironAction,
    GlobalResolveSystemSessionEnvironActionResult,
)
from ai.backend.manager.services.system_session_environ.service import (
    SystemSessionEnvironService,
)

__all__ = ("SystemSessionEnvironProcessors",)


class SystemSessionEnvironProcessors:
    """The read of the rows a session in a domain and project receives.

    It names no row and reads across the public, domain and project scopes at once, so it
    is global; the service stays because the per-key precedence is a branch, not a spec.
    """

    global_resolve: GlobalActionProcessor[
        GlobalResolveSystemSessionEnvironAction, GlobalResolveSystemSessionEnvironActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: SystemSessionEnvironService) -> None:
        self.global_resolve = group.global_scope(
            GlobalResolveSystemSessionEnvironAction, service.global_resolve
        )
