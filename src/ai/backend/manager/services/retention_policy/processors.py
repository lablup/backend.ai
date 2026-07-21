from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
    CreateRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.delete import (
    DeleteRetentionPolicyAction,
    DeleteRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.purge import (
    PurgeRetentionPolicyAction,
    PurgeRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.actions.search import (
    SearchRetentionPoliciesAction,
    SearchRetentionPoliciesActionResult,
)
from ai.backend.manager.services.retention_policy.actions.update import (
    UpdateRetentionPolicyAction,
    UpdateRetentionPolicyActionResult,
)
from ai.backend.manager.services.retention_policy.service import RetentionPolicyService


class RetentionPolicyProcessors(AbstractProcessorPackage):
    create: GlobalActionProcessor[CreateRetentionPolicyAction, CreateRetentionPolicyActionResult]
    update: GlobalActionProcessor[UpdateRetentionPolicyAction, UpdateRetentionPolicyActionResult]
    delete: GlobalActionProcessor[DeleteRetentionPolicyAction, DeleteRetentionPolicyActionResult]
    purge: GlobalActionProcessor[PurgeRetentionPolicyAction, PurgeRetentionPolicyActionResult]
    search: GlobalActionProcessor[
        SearchRetentionPoliciesAction, SearchRetentionPoliciesActionResult
    ]

    def __init__(
        self,
        service: RetentionPolicyService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create = GlobalActionProcessor(service.create, action_monitors)
        self.update = GlobalActionProcessor(service.update, action_monitors)
        self.delete = GlobalActionProcessor(service.delete, action_monitors)
        self.purge = GlobalActionProcessor(service.purge, action_monitors)
        self.search = GlobalActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRetentionPolicyAction.spec(),
            UpdateRetentionPolicyAction.spec(),
            DeleteRetentionPolicyAction.spec(),
            PurgeRetentionPolicyAction.spec(),
            SearchRetentionPoliciesAction.spec(),
        ]
