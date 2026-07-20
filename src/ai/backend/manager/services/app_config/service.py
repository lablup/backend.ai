from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.contexts.user import current_user
from ai.backend.common.identifier.user import UserID
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
    """Merge ``override`` onto ``base``: nested dicts recurse; everything else replaces whole.

    An ``override`` value replaces the ``base`` one entirely — lists included (no
    element-by-index blending), and an explicit ``None`` overwrites rather than being skipped.
    The key itself stays either way; nothing here removes one. Unlike
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


def _merge_configs(fragments: Sequence[AppConfigFragmentData]) -> dict[str, Any]:
    """Deep-merge fragment configs in ascending ``rank`` order.

    Nested dicts recurse; lists and scalars are replaced wholesale by the higher-rank
    fragment (a user's list overrides the lower scope's entirely — not by index). Keys are
    only added or replaced, never dropped, and callers reject an empty ``fragments`` before
    getting here — so ``{}`` back means every fragment's own ``config`` was ``{}``.
    """
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

        The only read the service offers — one name is a one-element request. One entry per
        requested name, in request order; a name repeated in the input is repeated in the
        output (each position resolves independently, never collapsed).

        With ``scope_arguments`` **and** a session user, the merge overlays that user's
        domain and user fragments on top of ``public``. Missing either one is the anonymous,
        pre-login read: only ``public`` fragments contribute, and no session is not an error.
        The user half of the scope always comes from the session, so a caller can only ever
        resolve their own config.

        All-or-nothing on ``AppConfigFragmentNotFound``: one requested name nothing
        contributes to fails the whole call. A partial result would have to mark the absent
        names somehow, and every way of doing that pushes the caller into branching on a
        second, quieter kind of failure.
        """
        user = current_user()
        if action.scope_arguments is None or user is None:
            # The caller named no scope: the anonymous, pre-login read.
            scope = None
        else:
            scope = ResolvedAppConfigScope(
                domain_id=action.scope_arguments.domain_id, user_id=UserID(user.user_id)
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
