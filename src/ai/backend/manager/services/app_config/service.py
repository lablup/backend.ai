from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.app_config_fragment.types import AppConfigScopeArguments
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


def _authorize_resolve_principal(scope: AppConfigScopeArguments | None) -> None:
    """Reject resolving on behalf of a user other than the acting one.

    Only ``user_id`` is checked: it selects which user-scope fragments overlay the merge, so
    resolving someone else's would hand back their config. ``domain_id`` is deliberately left
    unchecked — the handler is expected to derive it from the same principal. Superadmins may
    resolve any principal.

    Reported as ``AppConfigFragmentNotFound``, not a permission error: another user's config
    is not something this caller is forbidden to read, it is something that does not exist as
    far as they can see. The message is the one an empty resolve raises, word for word —
    naming the principal here would undo that.
    """
    user = current_user()
    if user is not None and user.is_superadmin:
        # Superadmins resolve any principal — nothing below applies to them.
        return
    if scope is None:
        # Anonymous, pre-login resolve: only public fragments contribute, so there is no
        # principal to authorize.
        return
    if user is None:
        raise UnreachableError("User context is not available")
    if user.user_id == scope.user_id:
        return
    raise AppConfigFragmentNotFound("No visible fragment contributes to this app config.")


def _merge_configs(fragments: Sequence[AppConfigFragmentData]) -> dict[str, Any]:
    """Deep-merge fragment configs in ascending ``rank`` order.

    Nested dicts recurse; lists and scalars are replaced wholesale by the higher-rank
    fragment (a user's list overrides the lower scope's entirely — not by index). Callers
    reject an empty ``fragments`` before getting here, so ``{}`` back means the fragments
    themselves merged to nothing.
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

    async def resolve_app_config(
        self, action: ResolveAppConfigAction
    ) -> ResolveAppConfigActionResult:
        """Resolve the merged ``AppConfig`` for ``config_name``.

        With a principal ``scope`` the merge overlays the caller's domain and user fragments
        on top of ``public``; with ``scope=None`` (anonymous, pre-login) only ``public``
        fragments contribute.

        ``AppConfigFragmentNotFound`` covers every way this comes back empty — the name is
        unregistered, nothing is visible at this scope, or the named principal is not the
        caller's. The three are deliberately indistinguishable.
        """
        _authorize_resolve_principal(action.scope_arguments)
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            [action.config_name], action.scope_arguments
        )
        if not fragments:
            raise AppConfigFragmentNotFound("No visible fragment contributes to this app config.")
        app_config = AppConfigData(
            config_name=action.config_name,
            fragments=fragments,
            merged_config=_merge_configs(fragments),
        )
        user_id = action.scope_arguments.user_id if action.scope_arguments is not None else None
        return ResolveAppConfigActionResult(app_config=app_config, _user_id=user_id)

    async def resolve_app_config_bulk(
        self, action: ResolveBulkAppConfigAction
    ) -> ResolveBulkAppConfigActionResult:
        """Resolve several merged ``AppConfig``s for one principal in a single query.

        One entry per requested ``config_name``, in request order — a name repeated in the
        input is repeated in the output (each position resolves independently, never
        collapsed). With ``scope=None`` (anonymous, pre-login) only ``public`` fragments
        contribute to every entry.

        All-or-nothing on ``AppConfigFragmentNotFound``: one requested name nothing
        contributes to fails the whole batch, exactly as it would resolved on its own. A
        partial result would have to mark the absent names somehow, and every way of doing
        that reads differently from the single-name path.
        """
        _authorize_resolve_principal(action.scope)
        fragments = await self._fragment_repository.list_visible_fragments_bulk(
            action.config_names, action.scope
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
        user_id = action.scope.user_id if action.scope is not None else None
        return ResolveBulkAppConfigActionResult(app_configs=app_configs, _user_id=user_id)
