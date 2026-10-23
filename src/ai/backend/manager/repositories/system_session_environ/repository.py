from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import SessionId
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.scopes import (
    SessionSystemSessionEnvironScope,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.system_session_environ.db_source.db_source import (
    SystemSessionEnvironDBSource,
)
from ai.backend.manager.repositories.system_session_environ.value_resolver import (
    SystemSessionEnvironValueResolverRegistry,
)
from ai.backend.manager.views.sokovan.lifecycle import SessionDataForStart

__all__ = ("SystemSessionEnvironRepository",)


class SystemSessionEnvironRepository:
    _db_source: SystemSessionEnvironDBSource
    _value_resolver_registry: SystemSessionEnvironValueResolverRegistry

    def __init__(
        self,
        v2_ops_provider: V2DBOpsProvider,
        value_resolver_registry: SystemSessionEnvironValueResolverRegistry,
    ) -> None:
        self._db_source = SystemSessionEnvironDBSource(v2_ops_provider)
        self._value_resolver_registry = value_resolver_registry

    async def resolve(
        self, sessions: Sequence[SessionDataForStart]
    ) -> Mapping[SessionId, Mapping[str, str]]:
        """The system session environ each starting session receives, keyed by session id."""
        effective_rows_by_scope = await self._effective_rows_by_scope([
            SessionSystemSessionEnvironScope(
                domain_id=session.domain_id, project_id=session.project_id
            )
            for session in sessions
        ])
        resolved_environ_by_session: dict[SessionId, dict[str, str]] = {}
        for session in sessions:
            effective_rows = effective_rows_by_scope[
                SessionSystemSessionEnvironScope(
                    domain_id=session.domain_id, project_id=session.project_id
                )
            ]
            resolved_environ_by_session[session.session_id] = {
                row.key: self._value_resolver_registry.resolve(row.value_source, session)
                for row in effective_rows
            }
        return resolved_environ_by_session

    async def resolve_rows(
        self, domain_id: DomainID, project_id: ProjectID
    ) -> list[SystemSessionEnvironData]:
        """The enabled row each key resolves to for a session in the domain and project."""
        scope = SessionSystemSessionEnvironScope(domain_id=domain_id, project_id=project_id)
        effective_rows_by_scope = await self._effective_rows_by_scope([scope])
        return effective_rows_by_scope[scope]

    async def _effective_rows_by_scope(
        self, scopes: Sequence[SessionSystemSessionEnvironScope]
    ) -> Mapping[SessionSystemSessionEnvironScope, list[SystemSessionEnvironData]]:
        """The enabled row each key resolves to at every scope, read in one query.

        Per key the row at the most specific scope wins: project, then domain, then public.
        """
        rows_in_scopes = await self._db_source.search_in_scopes(scopes)
        effective_rows_by_scope: dict[
            SessionSystemSessionEnvironScope, list[SystemSessionEnvironData]
        ] = {}
        for scope in scopes:
            matching_rows = [row for row in rows_in_scopes if self._scope_matches(scope, row)]
            matching_rows.sort(
                key=lambda row: SystemSessionEnvironScopeType.of_owner(row.scope_id).override_rank()
            )
            most_specific_row_by_key: dict[str, SystemSessionEnvironData] = {}
            for row in matching_rows:
                most_specific_row_by_key[row.key] = row
            effective_rows_by_scope[scope] = [
                row for row in most_specific_row_by_key.values() if row.enabled
            ]
        return effective_rows_by_scope

    def _scope_matches(
        self, scope: SessionSystemSessionEnvironScope, row: SystemSessionEnvironData
    ) -> bool:
        match SystemSessionEnvironScopeType.of_owner(row.scope_id):
            case SystemSessionEnvironScopeType.PUBLIC:
                return True
            case SystemSessionEnvironScopeType.DOMAIN:
                return row.scope_id == scope.domain_id
            case SystemSessionEnvironScopeType.PROJECT:
                return row.scope_id == scope.project_id
            case _:
                raise UnreachableError(
                    f"Unknown system session environ scope type of {row.scope_id}"
                )
