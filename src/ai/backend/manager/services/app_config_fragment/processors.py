from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_purge import (
    BulkPurgeAppConfigFragmentAction,
    BulkPurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_update import (
    BulkUpdateAppConfigFragmentAction,
    BulkUpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.create import (
    CreateAppConfigFragmentAction,
    CreateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.domain_scoped_search import (
    DomainScopedSearchAppConfigFragmentAction,
    DomainScopedSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.user_scoped_search import (
    UserScopedSearchAppConfigFragmentAction,
    UserScopedSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.service import (
    AppConfigFragmentService,
)


class AppConfigFragmentProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[CreateAppConfigFragmentAction, CreateAppConfigFragmentActionResult]
    get: SingleEntityActionProcessor[GetAppConfigFragmentAction, GetAppConfigFragmentActionResult]
    admin_search: ScopeActionProcessor[
        AdminSearchAppConfigFragmentAction, AdminSearchAppConfigFragmentActionResult
    ]
    domain_scoped_search: ScopeActionProcessor[
        DomainScopedSearchAppConfigFragmentAction, DomainScopedSearchAppConfigFragmentActionResult
    ]
    user_scoped_search: ScopeActionProcessor[
        UserScopedSearchAppConfigFragmentAction, UserScopedSearchAppConfigFragmentActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateAppConfigFragmentAction, UpdateAppConfigFragmentActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, PurgeAppConfigFragmentActionResult
    ]
    bulk_update: BulkActionProcessor[
        BulkUpdateAppConfigFragmentAction, BulkUpdateAppConfigFragmentActionResult
    ]
    bulk_purge: BulkActionProcessor[
        BulkPurgeAppConfigFragmentAction, BulkPurgeAppConfigFragmentActionResult
    ]

    def __init__(
        self,
        service: AppConfigFragmentService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Fragment writes are open to any authenticated user and gated by RBAC: a user
        # writes their own user-scope fragment, a domain admin their domain's, a superadmin
        # any (public is superadmin-only). The scope / single-entity / bulk RBAC validators
        # enforce that per operation.
        self.create = ScopeActionProcessor(
            service.create, action_monitors, validators=[validators.rbac.scope]
        )
        self.get = SingleEntityActionProcessor(
            service.get, action_monitors, validators=[validators.rbac.single_entity]
        )
        # admin_search is system-wide (all scopes) — gated by superadmin_required at the API
        # layer, so it carries no per-scope RBAC validator. Non-admins use the scoped
        # searches below, one per scope the fragments may be written at.
        self.admin_search = ScopeActionProcessor(service.admin_search, action_monitors)
        self.domain_scoped_search = ScopeActionProcessor(
            service.domain_scoped_search, action_monitors, validators=[validators.rbac.scope]
        )
        self.user_scoped_search = ScopeActionProcessor(
            service.user_scoped_search, action_monitors, validators=[validators.rbac.scope]
        )
        self.update = SingleEntityActionProcessor(
            service.update, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.purge = SingleEntityActionProcessor(
            service.purge, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.bulk_update = BulkActionProcessor(
            service.bulk_update, monitors=action_monitors, validators=[validators.rbac.bulk]
        )
        self.bulk_purge = BulkActionProcessor(
            service.bulk_purge, monitors=action_monitors, validators=[validators.rbac.bulk]
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAppConfigFragmentAction.spec(),
            GetAppConfigFragmentAction.spec(),
            AdminSearchAppConfigFragmentAction.spec(),
            DomainScopedSearchAppConfigFragmentAction.spec(),
            UserScopedSearchAppConfigFragmentAction.spec(),
            UpdateAppConfigFragmentAction.spec(),
            PurgeAppConfigFragmentAction.spec(),
            BulkUpdateAppConfigFragmentAction.spec(),
            BulkPurgeAppConfigFragmentAction.spec(),
        ]
