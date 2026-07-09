from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.services.app_config.actions.resolve import (
    ResolveAppConfigAction,
    ResolveAppConfigActionResult,
)
from ai.backend.manager.services.app_config.actions.resolve_bulk import (
    ResolveBulkAppConfigAction,
    ResolveBulkAppConfigActionResult,
)

__all__ = ("AppConfigService",)


def _recursive_override(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Merge ``override`` onto ``base``: nested dicts recurse; everything else replaces whole.

    A higher-rank value replaces the lower one entirely — lists included (no element-by-index
    blending), and an explicit ``None`` erases the inherited value (unset). Unlike
    :func:`ai.backend.common.utils.deep_merge`, which blends lists by index and ignores ``None``.
    """
    result: dict[str, Any] = dict(base)
    for key, override_value in override.items():
        base_value = result.get(key)
        if isinstance(base_value, Mapping) and isinstance(override_value, Mapping):
            result[key] = _recursive_override(base_value, override_value)
        else:
            result[key] = override_value
    return result


def _merge_configs(fragments: Sequence[AppConfigFragmentData]) -> dict[str, Any] | None:
    """Deep-merge fragment configs in ascending ``rank`` order; ``None`` when none contribute.

    Nested dicts recurse; lists and scalars are replaced wholesale by the higher-rank
    fragment (a user's list overrides the lower scope's entirely — not by index). ``None``
    marks a config name that is defined but left unconfigured for this scope, distinct from
    a fragment that merges to an empty ``{}``.
    """
    if not fragments:
        return None
    merged: dict[str, Any] = {}
    for fragment in fragments:
        merged = _recursive_override(merged, fragment.config)
    return merged


class AppConfigService:
    """Read-side service for the merged ``AppConfig`` view."""

    _fragment_repository: AppConfigFragmentRepository

    def __init__(self, fragment_repository: AppConfigFragmentRepository) -> None:
        self._fragment_repository = fragment_repository

    async def resolve_app_config(
        self, action: ResolveAppConfigAction
    ) -> ResolveAppConfigActionResult:
        """Resolve the merged ``AppConfig`` for ``config_name``.

        With a principal ``scope`` the merge overlays the caller's domain and user fragments
        on top of ``public``; with ``scope=None`` (anonymous, pre-login) only ``public``
        fragments contribute.
        """
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            [action.config_name], action.scope
        )
        app_config = AppConfigData(
            config_name=action.config_name,
            fragments=fragments,
            merged_config=_merge_configs(fragments),
        )
        user_id = action.scope.user_id if action.scope is not None else None
        return ResolveAppConfigActionResult(app_config=app_config, _user_id=user_id)

    async def resolve_app_config_bulk(
        self, action: ResolveBulkAppConfigAction
    ) -> ResolveBulkAppConfigActionResult:
        """Resolve several merged ``AppConfig``s for one principal in a single query.

        One entry per requested ``config_name``, in request order — a name repeated in the
        input is repeated in the output (each position resolves independently, never
        collapsed). With ``scope=None`` (anonymous, pre-login) only ``public`` fragments
        contribute to every entry.
        """
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            action.config_names, action.scope
        )
        app_configs: list[AppConfigData] = []
        for config_name in action.config_names:
            visible = [fragment for fragment in fragments if fragment.config_name == config_name]
            app_configs.append(
                AppConfigData(
                    config_name=config_name,
                    fragments=visible,
                    merged_config=_merge_configs(visible),
                )
            )
        user_id = action.scope.user_id if action.scope is not None else None
        return ResolveBulkAppConfigActionResult(app_configs=app_configs, _user_id=user_id)
