from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.services.app_config.actions.search import (
    AnonymousSearchAppConfigsAction,
    SearchAppConfigsAction,
    SearchAppConfigsActionResult,
)
from ai.backend.manager.services.app_config.service import AppConfigService


class AppConfigProcessors:
    """Two reads of the same merge, told apart by who may ask.

    The signed-in read is answered for by the user's scope; the anonymous one names no
    principal, which is what limits it to the published fragments.
    """

    search_app_configs: ScopeActionProcessor[SearchAppConfigsAction, SearchAppConfigsActionResult]
    anonymous_search_app_configs: ScopeActionProcessor[
        AnonymousSearchAppConfigsAction, SearchAppConfigsActionResult
    ]

    def __init__(
        self,
        # No ops here, so the group's data type is unused.
        group: ProcessorGroup[Any],
        service: AppConfigService,
    ) -> None:
        self.search_app_configs = group.scope(SearchAppConfigsAction, service.search_app_configs)
        self.anonymous_search_app_configs = group.anonymous_scope(
            AnonymousSearchAppConfigsAction, service.anonymous_search_app_configs
        )
