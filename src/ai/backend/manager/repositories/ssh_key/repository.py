from __future__ import annotations

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.errors.ssh_keypair import SSHKeyNotFound
from ai.backend.manager.models.ssh_keypair.creators import SSHKeypairCreator
from ai.backend.manager.models.ssh_keypair.queriers import (
    DefaultSSHKeypairQuerier,
    SSHKeyQuerier,
)
from ai.backend.manager.models.ssh_keypair.scopes import UserSSHKeypairTarget
from ai.backend.manager.models.ssh_keypair.updaters import (
    SSHKeyDefaultClearUpdater,
    SSHKeyDefaultSetUpdater,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

ssh_key_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SSH_KEY_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class SSHKeyRepository:
    """The SSH keys of a user, one of them the default the sessions use."""

    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    @ssh_key_repository_resilience.apply()
    async def upload(self, user_id: UserID, public_key: SSHPublicKey) -> SSHKeypairData:
        """Add a public key to the user. It becomes the default only when the user has none."""
        async with self._ops.write_ops() as w:
            designated = await w.query_owned_fields(DefaultSSHKeypairQuerier(), [user_id])
            return await w.create_field(
                user_id,
                SSHKeypairCreator(
                    public_key=public_key,
                    private_key=None,
                    is_default=user_id not in designated,
                ),
            )

    @ssh_key_repository_resilience.apply()
    async def switch_default(self, ssh_key_id: SSHKeypairID) -> SSHKeypairData:
        """Make one SSH key its user's default, unmarking the previous one."""
        async with self._ops.write_ops() as w:
            target = await w.query_field_data(SSHKeyQuerier(ssh_key_id=ssh_key_id))
            if target is None:
                raise SSHKeyNotFound(f"SSH key {ssh_key_id} not found")
            await w.batch_update_in_scopes(
                [UserSSHKeypairTarget(user_id=target.user_id)], SSHKeyDefaultClearUpdater()
            )
            switched = await w.update_data(SSHKeyDefaultSetUpdater(ssh_key_id))
            if switched is None:
                raise SSHKeyNotFound(f"SSH key {ssh_key_id} not found")
            return switched
