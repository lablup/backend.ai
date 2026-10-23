"""System session environ domain adapter - Pydantic-in/Pydantic-out transport layer.

Shared between the GraphQL resolvers and REST v2 handlers.
"""

from __future__ import annotations

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminResolveSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    ResolveSystemSessionEnvironPayload,
    SystemSessionEnvironNode,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo,
    SystemSessionEnvironScopeType,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.services.system_session_environ.actions.global_resolve import (
    GlobalResolveSystemSessionEnvironAction,
)
from ai.backend.manager.services.system_session_environ.processors import (
    SystemSessionEnvironProcessors,
)

__all__ = ("SystemSessionEnvironAdapter",)


class SystemSessionEnvironAdapter(BaseAdapter):
    """Adapter for system session environ operations."""

    _system_session_environ: SystemSessionEnvironProcessors

    def __init__(self, system_session_environ: SystemSessionEnvironProcessors) -> None:
        self._system_session_environ = system_session_environ

    async def global_resolve(
        self, input: AdminResolveSystemSessionEnvironInput
    ) -> ResolveSystemSessionEnvironPayload:
        """Read the rows a session in the domain and project receives, one per key."""
        result = await self._system_session_environ.global_resolve.run(
            GlobalResolveSystemSessionEnvironAction(
                domain_id=input.domain_id, project_id=input.project_id
            )
        )
        return ResolveSystemSessionEnvironPayload(
            items=[
                SystemSessionEnvironNode(
                    entity_id=row.id,
                    key=row.key,
                    value_source=row.value_source,
                    scope=SystemSessionEnvironScopeInfo(
                        scope_type=SystemSessionEnvironScopeType.of_owner(row.scope_id),
                        scope_id=SystemSessionEnvironScopeID(row.scope_id),
                    ),
                )
                for row in result.effective_rows
            ]
        )
