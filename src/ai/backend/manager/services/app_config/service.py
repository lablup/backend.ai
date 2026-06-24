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
