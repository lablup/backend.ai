from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.common.data.system_session_environ.types import SystemSessionEnvironScopeType
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import SessionId
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.system_session_environ.scopes import (
    SessionSystemSessionEnvironScope,
)
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.manager.models.system_session_environ.searchers import (
    SystemSessionEnvironSearcher,
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
        environs_applied_by_scope = await self._environs_applied_by_scope([
            SessionSystemSessionEnvironScope(
                domain_id=session.domain_id, project_id=session.project_id
            )
            for session in sessions
        ])
        resolved_environ_by_session: dict[SessionId, dict[str, str]] = {}
        for session in sessions:
            environs_applied_to_session = environs_applied_by_scope[
                SessionSystemSessionEnvironScope(
                    domain_id=session.domain_id, project_id=session.project_id
                )
            ]
            resolved_environ_by_session[session.session_id] = {
                environ.key: self._value_resolver_registry.resolve(environ.value_source, session)
                for environ in environs_applied_to_session
            }
        return resolved_environ_by_session

    async def _environs_applied_by_scope(
        self, scopes: Sequence[SessionSystemSessionEnvironScope]
    ) -> Mapping[SessionSystemSessionEnvironScope, list[SystemSessionEnvironData]]:
        """The live environ each key resolves to at every scope, read in one query.

        Per key the environ at the most specific scope wins: project, then domain, then public.
        """
        environs_in_any_scope = await self._db_source.search_in_scopes(
            scopes,
            SystemSessionEnvironSearcher(
                pagination=NoPagination(),
                conditions=[SystemSessionEnvironSearchableFields.own.deleted_at.filter.is_null()],
            ),
        )
        environs_applied_by_scope: dict[
            SessionSystemSessionEnvironScope, list[SystemSessionEnvironData]
        ] = {}
        for scope in scopes:
            environs_visible_to_scope = [
                environ
                for environ in environs_in_any_scope
                if self._is_visible_to_scope(scope, environ)
            ]
            environs_visible_to_scope.sort(
                key=lambda environ: SystemSessionEnvironScopeType.of_owner(
                    environ.scope_id
                ).override_rank()
            )
            most_specific_environ_by_key: dict[str, SystemSessionEnvironData] = {}
            for environ in environs_visible_to_scope:
                most_specific_environ_by_key[environ.key] = environ
            environs_applied_by_scope[scope] = list(most_specific_environ_by_key.values())
        return environs_applied_by_scope

    def _is_visible_to_scope(
        self, scope: SessionSystemSessionEnvironScope, environ: SystemSessionEnvironData
    ) -> bool:
        match SystemSessionEnvironScopeType.of_owner(environ.scope_id):
            case SystemSessionEnvironScopeType.PUBLIC:
                return True
            case SystemSessionEnvironScopeType.DOMAIN:
                return environ.scope_id == scope.domain_id
            case SystemSessionEnvironScopeType.PROJECT:
                return environ.scope_id == scope.project_id
            case _:
                raise UnreachableError(
                    f"Unknown system session environ scope type of {environ.scope_id}"
                )
