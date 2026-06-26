from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.common.utils import deep_merge
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigResolveScope
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigAction,
    ResolveAppConfigActionResult,
)
from ai.backend.manager.services.app_config.actions.resolve_bulk import (
    ResolveBulkAppConfigAction,
    ResolveBulkAppConfigActionResult,
)
from ai.backend.manager.services.app_config.actions.resolve_public import (
    ResolvePublicAppConfigAction,
    ResolvePublicAppConfigActionResult,
)

__all__ = ("AppConfigService",)


class AppConfigService:
    """Read-side service for the merged ``AppConfig`` view (BEP-1052).

    Resolves the merged config for a ``(user, config_name)`` by querying the domain-visible
    scope (public + domain) and the user-visible scope (the user's own fragment)
    independently, then deep-merging both in ``rank`` order. Reads are unconditional — no
    allow-list / write-gate applies.
    """

    _fragment_repository: AppConfigFragmentRepository

    def __init__(self, fragment_repository: AppConfigFragmentRepository) -> None:
        self._fragment_repository = fragment_repository

    @staticmethod
    def _merge_configs(fragments: Sequence[AppConfigFragmentData]) -> dict[str, Any] | None:
        """Deep-merge fragment configs in ascending ``rank`` order; empty result is ``None``.

        ``fragments`` must be pre-ordered low -> high so higher-rank fragments override.
        """
        merged = dict(deep_merge(*(fragment.config for fragment in fragments)))
        return merged or None

    async def resolve(self, action: ResolveAppConfigAction) -> ResolveAppConfigActionResult:
        """Resolve the merged ``AppConfig`` for ``(user, config_name)``.

        The domain-visible scope (public + domain) and the user-visible scope (the user's
        own fragment) are fetched together in a single ``rank``-ordered query, then
        deep-merged. An unregistered name simply yields an empty merge (``config`` is
        ``None``).
        """
        fragments = await self._fragment_repository.list_visible_fragments(
            action.config_name,
            AppConfigResolveScope(domain_id=action.domain_id, user_id=action.user_id),
        )
        app_config = AppConfigData(
            config_name=action.config_name,
            fragments=fragments,
            config=self._merge_configs(fragments),
        )
        return ResolveAppConfigActionResult(app_config=app_config, user_id=action.user_id)

    async def resolve_bulk(
        self, action: ResolveBulkAppConfigAction
    ) -> ResolveBulkAppConfigActionResult:
        """Resolve several merged ``AppConfig``s for one principal in a single query.

        Fetches the visible fragments of all ``config_names`` at once, groups them by name,
        and deep-merges each in ``rank`` order. Returns one ``AppConfigData`` per requested
        name, in request order (an unregistered name yields ``config = None``).
        """
        scope = AppConfigResolveScope(domain_id=action.domain_id, user_id=action.user_id)
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            action.config_names, scope
        )
        grouped: dict[str, list[AppConfigFragmentData]] = {}
        for fragment in fragments:
            grouped.setdefault(fragment.config_name, []).append(fragment)
        app_configs = [
            AppConfigData(
                config_name=config_name,
                fragments=grouped.get(config_name, []),
                config=self._merge_configs(grouped.get(config_name, [])),
            )
            for config_name in action.config_names
        ]
        return ResolveBulkAppConfigActionResult(app_configs=app_configs, user_id=action.user_id)

    async def resolve_public(
        self, action: ResolvePublicAppConfigAction
    ) -> ResolvePublicAppConfigActionResult:
        """Resolve the merged ``AppConfig`` from ``public`` fragments only (anonymous read).

        No principal is involved, so only public-scope documents are fetched (``rank``-ordered)
        and deep-merged. An unregistered name yields an empty merge (``config`` is ``None``).
        """
        fragments = await self._fragment_repository.list_public_fragments(action.config_name)
        app_config = AppConfigData(
            config_name=action.config_name,
            fragments=fragments,
            config=self._merge_configs(fragments),
        )
        return ResolvePublicAppConfigActionResult(app_config=app_config)
