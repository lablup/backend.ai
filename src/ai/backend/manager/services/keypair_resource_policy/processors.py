from __future__ import annotations

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_keypair_resource_policy import (
    GetKeypairResourcePolicyAction,
)
from ai.backend.manager.services.keypair_resource_policy.actions.get_my_keypair_resource_policy import (
    GetMyKeypairResourcePolicyAction,
    GetMyKeypairResourcePolicyActionResult,
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
from ai.backend.manager.services.keypair_resource_policy.service import (
    KeypairResourcePolicyService,
)


class KeypairResourcePolicyProcessors:
    get_keypair_resource_policy: GlobalActionProcessor[
        GetKeypairResourcePolicyAction, EntityOpsResult[KeyPairResourcePolicyData]
    ]
    get_my_keypair_resource_policy: ActionProcessor[
        GetMyKeypairResourcePolicyAction, GetMyKeypairResourcePolicyActionResult
    ]
    search_keypair_resource_policies: GlobalActionProcessor[
        SearchKeypairResourcePoliciesAction, BatchOpsResult[KeyPairResourcePolicyData]
    ]
    create_keypair_resource_policy: GlobalActionProcessor[
        CreateKeyPairResourcePolicyAction, CreatedEntityOpsResult[KeyPairResourcePolicyData]
    ]
    update_keypair_resource_policy: GlobalActionProcessor[
        UpdateKeyPairResourcePolicyAction, EntityOpsResult[KeyPairResourcePolicyData]
    ]
    purge_keypair_resource_policy: GlobalActionProcessor[
        PurgeKeyPairResourcePolicyAction, EntityOpsResult[KeyPairResourcePolicyData]
    ]

    def __init__(
        self,
        service: KeypairResourcePolicyService,
        action_monitors: list[ActionMonitor],
        group: ProcessorGroup[KeyPairResourcePolicyData],
    ) -> None:
        self.get_keypair_resource_policy = group.global_get_ops(GetKeypairResourcePolicyAction)
        self.get_my_keypair_resource_policy = ActionProcessor(
            service.get_my_keypair_resource_policy, action_monitors
        )
        self.search_keypair_resource_policies = group.global_search_ops(
            SearchKeypairResourcePoliciesAction
        )
        self.create_keypair_resource_policy = group.global_create_ops(
            CreateKeyPairResourcePolicyAction
        )
        self.update_keypair_resource_policy = group.global_update_ops(
            UpdateKeyPairResourcePolicyAction
        )
        self.purge_keypair_resource_policy = group.global_purge_ops(
            PurgeKeyPairResourcePolicyAction
        )
