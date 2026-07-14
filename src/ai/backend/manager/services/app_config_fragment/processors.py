from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.app_config_fragment.actions.admin_search import (
    AdminSearchAppConfigFragmentAction,
    AdminSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.bulk_create import (
    BulkCreateAppConfigFragmentAction,
    BulkCreateAppConfigFragmentActionResult,
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
from ai.backend.manager.services.app_config_fragment.actions.get import (
    GetAppConfigFragmentAction,
    GetAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.purge import (
    PurgeAppConfigFragmentAction,
    PurgeAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.scoped_search import (
    ScopedSearchAppConfigFragmentAction,
    ScopedSearchAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.actions.update import (
    UpdateAppConfigFragmentAction,
    UpdateAppConfigFragmentActionResult,
)
from ai.backend.manager.services.app_config_fragment.service import (
    AppConfigFragmentService,
)
from ai.backend.manager.services.app_config_fragment.validators import (
    PublicAppConfigFragmentWriteValidator,
)


class AppConfigFragmentProcessors(AbstractProcessorPackage):
    create: ScopeActionProcessor[CreateAppConfigFragmentAction, CreateAppConfigFragmentActionResult]
    get: SingleEntityActionProcessor[GetAppConfigFragmentAction, GetAppConfigFragmentActionResult]
    admin_search: ScopeActionProcessor[
        AdminSearchAppConfigFragmentAction, AdminSearchAppConfigFragmentActionResult
    ]
    scoped_search: BulkActionProcessor[
        ScopedSearchAppConfigFragmentAction, ScopedSearchAppConfigFragmentActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateAppConfigFragmentAction, UpdateAppConfigFragmentActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeAppConfigFragmentAction, PurgeAppConfigFragmentActionResult
    ]
    bulk_create: BulkActionProcessor[
        BulkCreateAppConfigFragmentAction, BulkCreateAppConfigFragmentActionResult
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
        config_provider: ManagerConfigProvider,
    ) -> None:
        # Writes are authorized by RBAC (BEP-1052): create acts at the fragment's target
        # scope (own user / domain / superadmin-only public), while update / purge act on
        # the fragment entity whose scope is resolved through its scope binding. Reads stay
        # on the allow-list read tiers, so get / admin_search / scoped_search carry no RBAC
        # validator. Bulk create has no pre-existing targets, so the target-based bulk
        # validator cannot authorize it — only bulk update / purge are wired.
        #
        # A public fragment is global-scoped and has no RBAC scope element, so the generic
        # scope-chain validator cannot represent it; the public guard runs first to keep
        # public writes superadmin-only and defers user / domain scopes to the scope check.
        public_write_guard = PublicAppConfigFragmentWriteValidator(config_provider)
        self.create = ScopeActionProcessor(
            service.create,
            action_monitors,
            validators=[public_write_guard, validators.rbac.scope],
        )
        self.get = SingleEntityActionProcessor(service.get, action_monitors)
        self.admin_search = ScopeActionProcessor(service.admin_search, action_monitors)
        self.scoped_search = BulkActionProcessor(service.scoped_search, monitors=action_monitors)
        self.update = SingleEntityActionProcessor(
            service.update, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.purge = SingleEntityActionProcessor(
            service.purge, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.bulk_create = BulkActionProcessor(service.bulk_create, monitors=action_monitors)
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
            ScopedSearchAppConfigFragmentAction.spec(),
            UpdateAppConfigFragmentAction.spec(),
            PurgeAppConfigFragmentAction.spec(),
            BulkCreateAppConfigFragmentAction.spec(),
            BulkUpdateAppConfigFragmentAction.spec(),
            BulkPurgeAppConfigFragmentAction.spec(),
        ]
