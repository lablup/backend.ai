from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import ResolvedAppConfigScope
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigsAction,
    ResolveAppConfigsActionResult,
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

    async def resolve_app_configs(
        self, action: ResolveAppConfigsAction
    ) -> ResolveAppConfigsActionResult:
        """Resolve the merged ``AppConfig`` for each of ``config_names`` in a single query.

        One entry per requested name, in request order; a repeated name is repeated in the
        output. Without both ``scope_arguments`` and ``user_id`` this is the anonymous,
        pre-login read — only ``public`` fragments contribute. A name nothing contributes to
        fails the whole call with ``AppConfigFragmentNotFound``.
        """
        if action.scope_arguments is None or action.user_id is None:
            # Either half missing is the anonymous, pre-login read.
            scope = None
        else:
            scope = ResolvedAppConfigScope(
                domain_id=action.scope_arguments.domain_id, user_id=action.user_id
            )
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            action.config_names, scope
        )
        app_configs: list[AppConfigData] = []
        for config_name in action.config_names:
            visible = [fragment for fragment in fragments if fragment.config_name == config_name]
            if not visible:
                raise AppConfigFragmentNotFound(
                    "No visible fragment contributes to this app config."
                )
            app_configs.append(
                AppConfigData(
                    config_name=config_name,
                    fragments=visible,
                    merged_config=_merge_configs(visible),
                )
            )
        return ResolveAppConfigsActionResult(
            app_configs=app_configs, _user_id=scope.user_id if scope is not None else None
        )
