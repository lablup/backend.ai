from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import PublicActionProcessor
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
    PublicListSystemSessionEnvironValueSourcesActionResult,
)
from ai.backend.manager.services.system_session_environ.service import SystemSessionEnvironService

__all__ = ("SystemSessionEnvironProcessors",)


class SystemSessionEnvironProcessors:
    public_list_value_sources: PublicActionProcessor[
        PublicListSystemSessionEnvironValueSourcesAction,
        PublicListSystemSessionEnvironValueSourcesActionResult,
    ]

    def __init__(self, group: ProcessorGroup[Any], service: SystemSessionEnvironService) -> None:
        self.public_list_value_sources = group.public(
            PublicListSystemSessionEnvironValueSourcesAction, service.public_list_value_sources
        )
