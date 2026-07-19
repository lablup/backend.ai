from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
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
    create: ActionProcessor[CreateRetentionPolicyAction, CreateRetentionPolicyActionResult]
    update: ActionProcessor[UpdateRetentionPolicyAction, UpdateRetentionPolicyActionResult]
    delete: ActionProcessor[DeleteRetentionPolicyAction, DeleteRetentionPolicyActionResult]
    purge: ActionProcessor[PurgeRetentionPolicyAction, PurgeRetentionPolicyActionResult]
    search: ActionProcessor[SearchRetentionPoliciesAction, SearchRetentionPoliciesActionResult]

    def __init__(
        self,
        service: RetentionPolicyService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = ActionProcessor(service.update, action_monitors)
        self.delete = ActionProcessor(service.delete, action_monitors)
        self.purge = ActionProcessor(service.purge, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateRetentionPolicyAction.spec(),
            UpdateRetentionPolicyAction.spec(),
            DeleteRetentionPolicyAction.spec(),
            PurgeRetentionPolicyAction.spec(),
            SearchRetentionPoliciesAction.spec(),
        ]
