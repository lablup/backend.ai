from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config.actions.get import (
    GetAppConfigsAction,
    GetAppConfigsActionResult,
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
    """Read-side service for the merged ``AppConfig`` view."""

    _fragment_repository: AppConfigFragmentRepository

    def __init__(self, fragment_repository: AppConfigFragmentRepository) -> None:
        self._fragment_repository = fragment_repository

    async def get_app_configs(self, action: GetAppConfigsAction) -> GetAppConfigsActionResult:
        """Get the merged ``AppConfig`` for each of ``config_names``.

        One entry per requested name, in request order; a repeated name is repeated in the
        output. Without a ``user_id`` only ``public`` fragments contribute. A name nothing
        contributes to yields an empty merge rather than failing the whole call.
        """
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            action.config_names, action.user_id
        )
        app_configs: list[AppConfigData] = []
        for config_name in action.config_names:
            visible = [fragment for fragment in fragments if fragment.config_name == config_name]
            app_configs.append(
                AppConfigData(
                    config_name=config_name,
                    merged_config=_merge_configs(visible),
                )
            )
        return GetAppConfigsActionResult(app_configs=app_configs, _user_id=action.user_id)
