"""System session environ domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    ListSystemSessionEnvironValueSourcesPayload,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.services.system_session_environ.actions.public_list_value_sources import (
    PublicListSystemSessionEnvironValueSourcesAction,
)
from ai.backend.manager.services.system_session_environ.processors import (
    SystemSessionEnvironProcessors,
)

__all__ = ("SystemSessionEnvironAdapter",)


class SystemSessionEnvironAdapter(BaseAdapter):
    _system_session_environ: SystemSessionEnvironProcessors

    def __init__(self, system_session_environ: SystemSessionEnvironProcessors) -> None:
        self._system_session_environ = system_session_environ

    async def public_list_value_sources(self) -> ListSystemSessionEnvironValueSourcesPayload:
        result = await self._system_session_environ.public_list_value_sources.run(
            PublicListSystemSessionEnvironValueSourcesAction()
        )
        return ListSystemSessionEnvironValueSourcesPayload(
            items=[value_source.value for value_source in result.value_sources]
        )
