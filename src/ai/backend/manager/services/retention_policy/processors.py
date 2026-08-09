from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.services.retention_policy.actions.create import (
    CreateRetentionPolicyAction,
)
from ai.backend.manager.services.retention_policy.actions.delete import (
    DeleteRetentionPolicyAction,
)
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

    create: GlobalActionProcessor[
        CreateRetentionPolicyAction,
        CreatedEntityOpsResult[RetentionPolicyData],
    ]
    update: GlobalActionProcessor[
        UpdateRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    delete: GlobalActionProcessor[
        DeleteRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    purge: GlobalActionProcessor[
        PurgeRetentionPolicyAction,
        EntityOpsResult[RetentionPolicyData],
    ]
    search: GlobalActionProcessor[
        SearchRetentionPoliciesAction,
        BatchOpsResult[RetentionPolicyData],
    ]

    def __init__(self, group: ProcessorGroup[RetentionPolicyData]) -> None:
        self.create = group.global_create_ops(CreateRetentionPolicyAction)
        self.update = group.global_update_ops(UpdateRetentionPolicyAction)
        self.delete = group.global_purge_ops(DeleteRetentionPolicyAction)
        self.purge = group.global_purge_ops(PurgeRetentionPolicyAction)
        self.search = group.global_search_ops(SearchRetentionPoliciesAction)
