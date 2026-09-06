from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, EntityOpsResult
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.services.client_ip_masking.actions.purge import (
    PurgeClientIPMaskingPolicyAction,
)
from ai.backend.manager.services.client_ip_masking.actions.search import (
    SearchClientIPMaskingPoliciesAction,
)
from ai.backend.manager.services.client_ip_masking.actions.upsert import (
    UpsertClientIPMaskingPolicyAction,
)


class ClientIPMaskingProcessors:
    """Every operation runs against ops: the policies carry no rule of their own."""

    global_search: GlobalActionProcessor[
        SearchClientIPMaskingPoliciesAction, BatchOpsResult[ClientIPMaskingPolicyData]
    ]
    global_upsert: GlobalActionProcessor[
        UpsertClientIPMaskingPolicyAction, EntityOpsResult[ClientIPMaskingPolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeClientIPMaskingPolicyAction, EntityOpsResult[ClientIPMaskingPolicyData]
    ]

    def __init__(self, group: ProcessorGroup[ClientIPMaskingPolicyData]) -> None:
        self.global_search = group.global_search_ops(SearchClientIPMaskingPoliciesAction)
        self.global_upsert = group.global_upsert_ops(UpsertClientIPMaskingPolicyAction)
        self.purge = group.entity_purge_ops(PurgeClientIPMaskingPolicyAction)
