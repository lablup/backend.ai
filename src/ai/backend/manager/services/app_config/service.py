from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigFragmentData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.app_config.actions.search import (
    AnonymousSearchAppConfigsAction,
    SearchAppConfigsAction,
    SearchAppConfigsActionResult,
)

__all__ = ("AppConfigService",)


def _recursive_override(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``override`` onto ``base``: nested dicts recurse, everything else replaces whole.

    Lists replace wholesale (no per-index blending) and an explicit ``None`` overwrites rather
    than being skipped — unlike :func:`ai.backend.common.utils.deep_merge`.
    """
    result: dict[str, Any] = dict(base)
    for key, override_value in override.items():
        base_value = result.get(key)
        if isinstance(base_value, Mapping) and isinstance(override_value, Mapping):
            result[key] = _recursive_override(base_value, override_value)
        else:
            result[key] = override_value
    return result


def _merge_configs(fragments: Sequence[AppConfigFragmentData]) -> dict[str, Any]:
    """Deep-merge fragment configs, lowest ``rank`` first — the caller passes them ordered."""
    merged: dict[str, Any] = {}
    for fragment in fragments:
        merged = _recursive_override(merged, fragment.config)
    return merged


class AppConfigService:
    """Read-side service for the merged ``AppConfig`` view.

    The fragment read is a plain scoped search, so it runs against ops; what keeps a
    service here is the merge, which turns many rows into one value per name.
    """

    _repository: OpsRepository[AppConfigFragmentData]

    def __init__(self, repository: OpsRepository[AppConfigFragmentData]) -> None:
        self._repository = repository

    async def search_app_configs(
        self, action: SearchAppConfigsAction
    ) -> SearchAppConfigsActionResult:
        """The merged ``AppConfig`` for each of ``config_names``.

        One entry per requested name, in request order; a repeated name is repeated in the
        output. A name nothing contributes to yields an empty merge rather than failing
        the whole call.
        """
        return await self._merge(
            action.operation_scopes(), action.to_searcher(), action.config_names
        )

    async def anonymous_search_app_configs(
        self, action: AnonymousSearchAppConfigsAction
    ) -> SearchAppConfigsActionResult:
        """The merge a caller sees before signing in: published fragments only."""
        return await self._merge(
            action.operation_scopes(), action.to_searcher(), action.config_names
        )

    async def _merge(
        self,
        scopes: Sequence[OperationScope],
        searcher: Searcher[Any, AppConfigFragmentData],
        config_names: Sequence[str],
    ) -> SearchAppConfigsActionResult:
        """Group the found fragments by name and merge each name's own, which arrive rank-ordered."""
        fragments = (await self._repository.search_in_scopes(scopes, searcher)).items
        app_configs: list[AppConfigData] = []
        for config_name in config_names:
            visible = [fragment for fragment in fragments if fragment.config_name == config_name]
            app_configs.append(
                AppConfigData(
                    config_name=config_name,
                    config=_merge_configs(visible),
                )
            )
        return SearchAppConfigsActionResult(app_configs=app_configs)
