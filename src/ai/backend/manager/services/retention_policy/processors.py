from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.delete import (
    DeleteRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.get import GetRetentionPolicyAction
from ai.backend.manager.services.retention_policy.actions.purge import (
    PurgeRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.search import (
    SearchRetentionPoliciesAction,
)
from ai.backend.manager.services.retention_policy.actions.update import (
    UpdateRetentionPolicyAction,
)


class RetentionPolicyProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    get: SingleEntityActionProcessor[GetRetentionPolicyAction, EntityOpsResult[RetentionPolicyData]]
    global_create: GlobalActionProcessor[
        CreateRetentionPolicyAction,
        CreatedEntityOpsResult[RetentionPolicyData],
    ]
    update: SingleEntityActionProcessor[
        UpdateRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    delete: SingleEntityActionProcessor[
        DeleteRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    purge: SingleEntityActionProcessor[
        PurgeRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    global_search: GlobalActionProcessor[
        SearchRetentionPoliciesAction,
        BatchOpsResult[RetentionPolicyData],
    ]

    def __init__(self, group: ProcessorGroup[RetentionPolicyData]) -> None:
        self.get = group.single_get_ops(GetRetentionPolicyAction)
        self.global_create = group.global_create_ops(CreateRetentionPolicyAction)
        self.update = group.single_update_ops(UpdateRetentionPolicyAction)
        self.delete = group.entity_purge_ops(DeleteRetentionPolicyAction)
        self.purge = group.entity_purge_ops(PurgeRetentionPolicyAction)
        self.global_search = group.global_search_ops(SearchRetentionPoliciesAction)
