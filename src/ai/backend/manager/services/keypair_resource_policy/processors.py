from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.global_search_keypair_resource_policies import (
    GlobalSearchKeypairResourcePoliciesAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.lookup import (
    LookupKeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.purge_keypair_resource_policy import (
    PurgeKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.search_keypair_resource_policies import (
    SearchKeypairResourcePoliciesAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.update_keypair_resource_policy import (
    UpdateKeyPairResourcePolicyAction,
)


class KeypairResourcePolicyProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    lookup: LookupActionProcessor[
        LookupKeypairResourcePolicyAction, LookupOpsResult[KeyPairResourcePolicyData]
    ]
    search: ScopeActionProcessor[
        SearchKeypairResourcePoliciesAction, ScopedBatchOpsResult[KeyPairResourcePolicyData]
    ]
    global_search: GlobalActionProcessor[
        GlobalSearchKeypairResourcePoliciesAction, BatchOpsResult[KeyPairResourcePolicyData]
    ]
    global_create: GlobalActionProcessor[
        CreateKeyPairResourcePolicyAction, CreatedEntityOpsResult[KeyPairResourcePolicyData]
    ]
    update: SingleEntityActionProcessor[
        UpdateKeyPairResourcePolicyAction, EntityOpsResult[KeyPairResourcePolicyData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeKeyPairResourcePolicyAction, EntityOpsResult[KeyPairResourcePolicyData]
    ]

    def __init__(self, group: ProcessorGroup[KeyPairResourcePolicyData]) -> None:
        self.lookup = group.lookup_ops(LookupKeypairResourcePolicyAction)
        self.search = group.scope_search_ops(SearchKeypairResourcePoliciesAction)
        self.global_search = group.global_search_ops(GlobalSearchKeypairResourcePoliciesAction)
        self.global_create = group.global_create_ops(CreateKeyPairResourcePolicyAction)
        self.update = group.single_update_ops(UpdateKeyPairResourcePolicyAction)
        self.purge = group.entity_purge_ops(PurgeKeyPairResourcePolicyAction)
