from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.exception import BackendAIError, DomainNotFound
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.errors.resource import DomainDeletionFailed
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.models.domain.purgers import DomainKernelPurger, DomainPurger
from ai.backend.manager.models.domain.updaters import DomainDotfilesUpdater, DomainUpdater
from ai.backend.manager.models.group.creators import GroupCreator
from ai.backend.manager.models.group.row import ProjectType
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.db_source import DomainDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

domain_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.DOMAIN_REPOSITORY)),
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


class DomainRepository:
    _db: ExtendedAsyncSAEngine
    _db_source: DomainDBSource
    _v2_ops: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db = db
        self._db_source = DomainDBSource(db)
        self._v2_ops = v2_ops_provider

    @domain_repository_resilience.apply()
    async def create_domain(self, creator: DomainCreator) -> DomainData:
        """Register a domain together with the model-store project every domain has."""
        async with self._v2_ops.write_ops() as w:
            data = await w.create_role_managed_entity(creator)
            await w.create_role_managed_entity(
                GroupCreator(
                    name="model-store",
                    domain_id=data.id,
                    domain_name=data.name,
                    description="Model Store",
                    resource_policy="default",
                    type=ProjectType.MODEL_STORE,
                )
            )
            return data

    @domain_repository_resilience.apply()
    async def purge_domain(self, domain_id: DomainID, domain_name: str) -> DomainData:
        """Remove a domain and the kernel rows it left, in one transaction."""
        async with self._v2_ops.write_ops() as w:
            await w.batch_purge_in_global(DomainKernelPurger(name=domain_name))
            data = await w.purge_entity(DomainPurger(domain_id=domain_id, name=domain_name))
            if data is None:
                raise DomainDeletionFailed(f"Failed to delete domain: {domain_name}")
            return data

    @domain_repository_resilience.apply()
    async def create_domain_node(
        self, creator: DomainCreator, resource_group_ids: list[ResourceGroupID] | None = None
    ) -> DomainData:
        """Register a domain and the resource groups it may schedule on.

        The associations are written separately: an association row belongs to neither
        side of the pair, so the v2 ops layer has no primitive that writes one.
        """
        async with self._v2_ops.write_ops() as w:
            data = await w.create_role_managed_entity(creator)
        if resource_group_ids:
            async with self._db.begin_session() as session:
                await session.execute(
                    sa.insert(ResourceGroupForDomainRow),
                    [
                        {"resource_group_id": sgroup_id, "domain_id": data.id}
                        for sgroup_id in resource_group_ids
                    ],
                )
        return data

    @domain_repository_resilience.apply()
    async def update_domain_node(
        self,
        domain_id: DomainID,
        updater: DomainUpdater,
        sgroup_ids_to_add: Collection[ResourceGroupID] | None = None,
        sgroup_ids_to_remove: Collection[ResourceGroupID] | None = None,
    ) -> DomainData:
        """Edit a domain and the resource groups it may schedule on."""
        if sgroup_ids_to_add or sgroup_ids_to_remove:
            async with self._db.begin_session() as session:
                if sgroup_ids_to_add:
                    await session.execute(
                        sa.insert(ResourceGroupForDomainRow),
                        [
                            {"resource_group_id": sgroup_id, "domain_id": domain_id}
                            for sgroup_id in sgroup_ids_to_add
                        ],
                    )
                if sgroup_ids_to_remove:
                    await session.execute(
                        sa.delete(ResourceGroupForDomainRow).where(
                            (ResourceGroupForDomainRow.domain_id == domain_id)
                            & (
                                ResourceGroupForDomainRow.resource_group_id.in_(
                                    sgroup_ids_to_remove
                                )
                            )
                        ),
                    )
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise DomainNotFound(f"Domain not found: {updater.pk_value()}")
            return data

    @domain_repository_resilience.apply()
    async def update_dotfiles(self, updater: DomainDotfilesUpdater) -> DomainData:
        """Replace a domain's packed dotfile entries."""
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise DomainNotFound(f"Domain not found: {updater.pk_value()}")
            return data

    @domain_repository_resilience.apply()
    async def get_domain_id_by_name(self, name: DomainName) -> DomainID:
        return await self._db_source.get_domain_id_by_name(name)

    @domain_repository_resilience.apply()
    async def get_domain(self, domain_name: str) -> DomainData:
        """Get a single domain by name.

        Args:
            domain_name: The name of the domain to retrieve.

        Returns:
            DomainData for the domain.

        Raises:
            DomainNotFound: If the domain does not exist.
        """
        return await self._db_source.get_domain(domain_name)
