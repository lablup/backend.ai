from __future__ import annotations

from collections.abc import Collection

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
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupForDomainRelationCreator,
)
from ai.backend.manager.models.resource_group.purgers import (
    ResourceGroupForDomainRelationPurger,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.db_source import DomainDBSource
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider

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
    _v2_ops: DomainOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, domain_ops_provider: DomainOpsProvider) -> None:
        self._db = db
        self._db_source = DomainDBSource(db)
        self._v2_ops = domain_ops_provider

    @domain_repository_resilience.apply()
    async def purge_domain(self, domain_id: DomainID, domain_name: str) -> DomainData:
        """Remove a domain and the kernel rows it left, in one transaction."""
        async with self._v2_ops.write_ops() as w:
            await w.batch_purge_field_entities(domain_id, DomainKernelPurger(name=domain_name))
            data = await w.purge_entity(DomainPurger(domain_id=domain_id, name=domain_name))
            if data is None:
                raise DomainDeletionFailed(f"Failed to delete domain: {domain_name}")
            return data

    @domain_repository_resilience.apply()
    async def create_domain(self, creator: DomainCreator) -> DomainData:
        """Register a domain with the model-store project it is registered with."""
        async with self._v2_ops.write_ops() as w:
            return (await w.create_domain(creator)).domain

    @domain_repository_resilience.apply()
    async def create_domain_node(
        self, creator: DomainCreator, resource_group_ids: list[ResourceGroupID] | None = None
    ) -> DomainData:
        """Register a domain, the model-store project it is registered with, and the
        resource groups it may schedule on."""
        async with self._v2_ops.write_ops() as w:
            return (await w.create_domain(creator, resource_group_ids)).domain

    @domain_repository_resilience.apply()
    async def update_domain_node(
        self,
        domain_id: DomainID,
        updater: DomainUpdater,
        sgroup_ids_to_add: Collection[ResourceGroupID] | None = None,
        sgroup_ids_to_remove: Collection[ResourceGroupID] | None = None,
    ) -> DomainData:
        """Edit a domain and the resource groups it may schedule on."""
        async with self._v2_ops.write_ops() as w:
            if sgroup_ids_to_add:
                await w.create_relations(
                    ResourceGroupForDomainRelationCreator(),
                    [(domain_id, sgroup_id) for sgroup_id in sgroup_ids_to_add],
                )
            if sgroup_ids_to_remove:
                await w.purge_relations(
                    ResourceGroupForDomainRelationPurger(),
                    [(domain_id, sgroup_id) for sgroup_id in sgroup_ids_to_remove],
                )
            data = await w.update_data(updater)
            if data is None:
                raise DomainNotFound(f"Domain not found: {updater.target_id_value()}")
            return data

    @domain_repository_resilience.apply()
    async def update_dotfiles(self, updater: DomainDotfilesUpdater) -> DomainData:
        """Replace a domain's packed dotfile entries."""
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise DomainNotFound(f"Domain not found: {updater.target_id_value()}")
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
