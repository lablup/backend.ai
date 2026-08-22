from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.resource_group.types import (
    ResourceGroupData,
    ResourceGroupListResult,
    ResourceInfo,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import BatchPurger, Purger
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)
from ai.backend.manager.repositories.base.updater import Updater

from .db_source import ResourceGroupDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ResourceGroupRepository",)


resource_group_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SCALING_GROUP_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class ResourceGroupRepository:
    """Repository for resource group-related data access."""

    _db_source: ResourceGroupDBSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db_source = ResourceGroupDBSource(db)

    @resource_group_repository_resilience.apply()
    async def create_resource_group(
        self,
        creator: Creator[ResourceGroupRow],
    ) -> ResourceGroupData:
        """Creates a new resource group.

        Raises ScalingGroupConflict if a resource group with the same name already exists.
        """
        return await self._db_source.create_resource_group(creator)

    @resource_group_repository_resilience.apply()
    async def search_resource_groups(
        self,
        querier: BatchQuerier,
    ) -> ResourceGroupListResult:
        """Searches resource groups with total count."""
        return await self._db_source.search_resource_groups(querier=querier)

    @resource_group_repository_resilience.apply()
    async def get_resource_group_id_by_name(self, name: ResourceGroupName) -> ResourceGroupID:
        return await self._db_source.get_resource_group_id_by_name(name)

    @resource_group_repository_resilience.apply()
    async def get_resource_group_ids_by_names(
        self,
        names: list[ResourceGroupName],
    ) -> dict[ResourceGroupName, ResourceGroupID]:
        """Resolve resource group row IDs from names; missing names are absent."""
        return await self._db_source.get_resource_group_ids_by_names(names)

    @resource_group_repository_resilience.apply()
    async def get_resource_group_by_name(
        self,
        name: str,
    ) -> ResourceGroupData:
        """Get a single resource group by name (primary key).

        Args:
            name: The name of the resource group (primary key).

        Returns:
            ResourceGroupData for the requested resource group.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        return await self._db_source.get_resource_group_by_name(name=name)

    @resource_group_repository_resilience.apply()
    async def purge_resource_group(
        self,
        purger: Purger[ResourceGroupRow],
    ) -> ResourceGroupData:
        """Purges a resource group and all related sessions, routes, endpoints, and kernels.

        Raises ScalingGroupNotFound if resource group doesn't exist.
        """
        return await self._db_source.purge_resource_group(purger)

    @resource_group_repository_resilience.apply()
    async def update_resource_group(
        self,
        updater: Updater[ResourceGroupRow],
    ) -> ResourceGroupData:
        """Updates an existing resource group.

        Raises ScalingGroupNotFound if the resource group does not exist.
        """
        return await self._db_source.update_resource_group(updater)

    @resource_group_repository_resilience.apply()
    async def replace_default_deployment_options(
        self,
        name: ResourceGroupName,
        options: DeploymentOptions,
    ) -> DeploymentOptions:
        """Fully replace a resource group's ``default_deployment_options``.

        Returns the persisted :class:`DeploymentOptions` value via
        ``UPDATE ... RETURNING`` so this path does a single round-trip and
        does not re-materialise the surrounding resource group node.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        return await self._db_source.replace_default_deployment_options(name, options)

    @resource_group_repository_resilience.apply()
    async def replace_default_session_options(
        self,
        name: ResourceGroupName,
        options: DefaultSessionOptions,
    ) -> DefaultSessionOptions:
        """Fully replace a resource group's ``default_session_options``.

        Returns the persisted :class:`DefaultSessionOptions` value via
        ``UPDATE ... RETURNING`` so this path does a single round-trip
        and does not re-materialise the surrounding resource group node.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        return await self._db_source.replace_default_session_options(name, options)

    async def associate_resource_group_with_domains(
        self,
        binder: RBACScopeBinder[ResourceGroupForDomainRow],
    ) -> None:
        """Associates a resource group with multiple domains."""
        await self._db_source.associate_resource_group_with_domains(binder)

    async def disassociate_resource_group_with_domains(
        self,
        unbinder: RBACScopeEntityUnbinder[ResourceGroupForDomainRow],
    ) -> None:
        """Disassociates resource groups from a domain."""
        await self._db_source.disassociate_resource_group_with_domains(unbinder)

    async def check_resource_group_domain_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        domain_id: DomainID,
    ) -> bool:
        """Checks if a resource group is associated with a domain."""
        return await self._db_source.check_resource_group_domain_association_exists(
            resource_group_id=resource_group_id,
            domain_id=domain_id,
        )

    async def associate_resource_group_with_keypairs(
        self,
        bulk_creator: BulkCreator[ResourceGroupForKeypairsRow],
    ) -> None:
        """Associates a resource group with multiple keypairs."""
        await self._db_source.associate_resource_group_with_keypairs(bulk_creator)

    async def disassociate_resource_group_with_keypairs(
        self,
        purger: BatchPurger[ResourceGroupForKeypairsRow],
    ) -> None:
        """Disassociates a resource group from multiple keypairs."""
        await self._db_source.disassociate_resource_group_with_keypairs(purger)

    async def check_resource_group_keypair_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        access_key: str,
    ) -> bool:
        """Checks if a resource group is associated with a keypair."""
        return await self._db_source.check_resource_group_keypair_association_exists(
            resource_group_id, access_key
        )

    async def associate_resource_group_with_user_groups(
        self,
        binder: RBACScopeBinder[ResourceGroupForProjectRow],
    ) -> None:
        """Associates a resource group with multiple user groups (projects)."""
        await self._db_source.associate_resource_group_with_user_groups(binder)

    async def disassociate_resource_group_with_user_groups(
        self,
        unbinder: RBACScopeEntityUnbinder[ResourceGroupForProjectRow],
    ) -> None:
        """Disassociates resource groups from a project."""
        await self._db_source.disassociate_resource_group_with_user_groups(unbinder)

    async def check_resource_group_user_group_association_exists(
        self,
        resource_group_id: ResourceGroupID,
        user_group: UUID,
    ) -> bool:
        """Checks if a resource group is associated with a user group (project)."""
        return await self._db_source.check_resource_group_user_group_association_exists(
            resource_group_id=resource_group_id,
            user_group=user_group,
        )

    @resource_group_repository_resilience.apply()
    async def list_allowed_sgroups(
        self,
        *,
        domain_name: str,
        group: str,
        access_key: str,
    ) -> list[ResourceGroupData]:
        """List resource groups allowed for a user."""
        return await self._db_source.list_allowed_sgroups(
            domain_name=domain_name,
            group=group,
            access_key=access_key,
        )

    async def get_resource_info(
        self,
        resource_group: str,
    ) -> ResourceInfo:
        """Get aggregated resource information for a resource group.

        Args:
            resource_group: The name of the resource group.

        Returns:
            ResourceInfo containing capacity, used, and free resource metrics.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        return await self._db_source.get_resource_info(resource_group)

    # Allow / Disallow operations

    async def update_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
        add: list[ResourceGroupID],
        remove: list[ResourceGroupID],
    ) -> list[str]:
        """Atomically add/remove allowed resource groups for a domain."""
        return await self._db_source.update_allowed_resource_groups_for_domain(
            domain_name=domain_name,
            add=add,
            remove=remove,
        )

    async def update_allowed_resource_groups_for_project(
        self,
        project_id: UUID,
        add: list[ResourceGroupID],
        remove: list[ResourceGroupID],
    ) -> list[str]:
        """Atomically add/remove allowed resource groups for a project."""
        return await self._db_source.update_allowed_resource_groups_for_project(
            project_id=project_id,
            add=add,
            remove=remove,
        )

    async def update_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
        add: list[str],
        remove: list[str],
    ) -> list[str]:
        """Atomically add/remove allowed domains for a resource group."""
        return await self._db_source.update_allowed_domains_for_resource_group(
            resource_group_id=resource_group_id,
            add=add,
            remove=remove,
        )

    async def update_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
        add: list[UUID],
        remove: list[UUID],
    ) -> list[UUID]:
        """Atomically add/remove allowed projects for a resource group."""
        return await self._db_source.update_allowed_projects_for_resource_group(
            resource_group_id=resource_group_id,
            add=add,
            remove=remove,
        )

    async def get_allowed_resource_groups_for_domain(
        self,
        domain_name: str,
    ) -> list[str]:
        """Get allowed resource group names for a domain."""
        return await self._db_source.get_allowed_resource_groups_for_domain(domain_name)

    async def get_allowed_resource_groups_for_project(
        self,
        project_id: UUID,
    ) -> list[str]:
        """Get allowed resource group names for a project."""
        return await self._db_source.get_allowed_resource_groups_for_project(project_id)

    async def get_allowed_domains_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[str]:
        """Get allowed domain names for a resource group."""
        return await self._db_source.get_allowed_domains_for_resource_group(resource_group_id)

    async def get_allowed_projects_for_resource_group(
        self,
        resource_group_id: ResourceGroupID,
    ) -> list[UUID]:
        """Get allowed projects for a resource group."""
        return await self._db_source.get_allowed_projects_for_resource_group(resource_group_id)
