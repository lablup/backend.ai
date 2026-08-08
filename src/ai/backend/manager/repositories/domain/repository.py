from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from typing import cast, override

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import BackendAIError, DomainNotFound, InvalidAPIParameters
from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.domain.types import (
    DomainData,
    UserInfo,
)
from ai.backend.manager.data.permission.permission_defs import (
    DomainPermission,
    ScalingGroupPermission,
)
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainUpdateNotAllowed,
    InvalidDomainConfiguration,
)
from ai.backend.manager.models.domain import DomainRow, domains, get_domains
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.kernel import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.rbac import SystemScope
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    get_scaling_groups,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.pagination import NoPagination, OffsetPagination
from ai.backend.manager.repositories.base.purger import BatchPurger
from ai.backend.manager.repositories.base.querier import BatchQuerier, Querier
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.repositories.domain.db_source import DomainDBSource
from ai.backend.manager.repositories.domain.purgers import (
    DomainKernelBatchPurgerSpec,
    DomainPurgerSpec,
)
from ai.backend.manager.repositories.domain.types import DomainOperationScope, DomainSearchResult
from ai.backend.manager.repositories.group.creators import GroupCreatorSpec
from ai.backend.manager.repositories.ops.rbac.provider import (
    RBACOpsProvider,
    RBACWriteOps,
    ScopeCreation,
    ScopeDeletion,
)
from ai.backend.manager.repositories.permission_controller.role_manager import (
    ScopeSystemRoleData,
)
from ai.backend.manager.repositories.scaling_group.creators import (
    ScalingGroupForDomainCreatorSpec,
)


@dataclass
class DomainScopeCreation(ScopeCreation[DomainRow]):
    """Creates a domain row and the top-level scope the domain becomes."""

    spec: DomainCreatorSpec

    @override
    def creator(self) -> RBACEntityCreator[DomainRow]:
        return RBACEntityCreator(
            spec=self.spec,
            element_type=RBACElementType.DOMAIN,
            scope_ref=None,
        )

    @override
    def scope_of(self, row: DomainRow) -> ScopeRef:
        return ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=row.id)

    @override
    def system_roles_of(self, row: DomainRow) -> Collection[ScopeSystemRoleData]:
        return (row.to_data(),)


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
    _rbac_ops_provider: RBACOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._db_source = DomainDBSource(db)
        self._rbac_ops_provider = RBACOpsProvider(db)

    @domain_repository_resilience.apply()
    async def create_domain(self, creator: Creator[DomainRow]) -> DomainData:
        """
        Creates a new domain with model-store group.
        Validates domain creation permissions.
        """
        spec = cast(DomainCreatorSpec, creator.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            existing_domain = await w.query(Querier(row_class=DomainRow, pk_value=spec.name))
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{spec.name}' already exists")

            creation_result = await w.create_scope(DomainScopeCreation(spec=spec))
            data = creation_result.row.to_data()

            # Create model-store group for the domain
            await self._create_model_store_group(w, spec.name)

            return data

    @domain_repository_resilience.apply()
    async def modify_domain(self, updater: Updater[DomainRow]) -> DomainData:
        """
        Modifies an existing domain.
        Validates domain modification permissions.
        """
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)

            if result is None:
                raise DomainNotFound(f"Domain not found: {updater.pk_value}")
            return result.row.to_data()

    @domain_repository_resilience.apply()
    async def soft_delete_domain(self, domain_name: str) -> None:
        """
        Soft deletes a domain by setting is_active to False.
        Validates domain deletion permissions.
        """
        async with self._db.begin() as conn:
            update_query = (
                sa.update(domains).values({"is_active": False}).where(domains.c.name == domain_name)
            )
            result = await conn.execute(update_query)
            if result.rowcount == 0:
                raise DomainNotFound(f"Domain not found: {domain_name}")

    @domain_repository_resilience.apply()
    async def purge_domain(self, domain_name: str) -> None:
        """
        Permanently deletes a domain after validation checks.
        Validates domain purge permissions and prerequisites.
        """
        async with self._rbac_ops_provider.write_ops() as w:
            # Must run before the kernel cleanup below deletes the rows it inspects.
            if await self._domain_has_active_kernels(w, domain_name):
                raise DomainHasActiveKernels(
                    "Domain has some active kernels. Terminate them first."
                )

            await w.batch_purge(
                BatchPurger(spec=DomainKernelBatchPurgerSpec(domain_name=domain_name))
            )

            domain_id = await self._get_domain_id(w, domain_name)
            result = await w.delete_scope(
                ScopeDeletion(
                    purger=RBACEntityPurger(
                        spec=DomainPurgerSpec(domain_name=domain_name, domain_id=domain_id)
                    ),
                    scope=ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
                )
            )
            if result is None:
                raise DomainDeletionFailed(f"Failed to delete domain: {domain_name}")

    @domain_repository_resilience.apply()
    async def create_domain_node(
        self, creator: Creator[DomainRow], scaling_group_ids: list[ResourceGroupID] | None = None
    ) -> DomainData:
        """
        Creates a domain node with scaling groups.
        Validates domain node creation permissions.
        """
        spec = cast(DomainCreatorSpec, creator.spec)
        async with self._rbac_ops_provider.write_ops() as w:
            existing_domain = await w.query(Querier(row_class=DomainRow, pk_value=spec.name))
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{spec.name}' already exists")

            creation_result = await w.create_scope(DomainScopeCreation(spec=spec))
            domain_row = creation_result.row

            if scaling_group_ids:
                await w.bulk_create(
                    BulkCreator(
                        specs=[
                            ScalingGroupForDomainCreatorSpec(
                                resource_group_id=sgroup_id,
                                domain_id=domain_row.id,
                            )
                            for sgroup_id in scaling_group_ids
                        ]
                    )
                )

            return domain_row.to_data()

    @domain_repository_resilience.apply()
    async def modify_domain_node(
        self,
        updater: Updater[DomainRow],
        sgroup_ids_to_add: set[ResourceGroupID] | None = None,
        sgroup_ids_to_remove: set[ResourceGroupID] | None = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes.
        Validates domain node modification permissions.
        """
        domain_name = str(updater.pk_value)
        async with self._db.begin_session() as session:
            domain_id = await session.scalar(
                sa.select(DomainRow.id).where(DomainRow.name == domain_name)
            )
            if domain_id is None:
                raise DomainNotFound(f"Domain not found (id:{domain_name})")

            if sgroup_ids_to_add:
                await session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"resource_group_id": sgroup_id, "domain_id": domain_id}
                        for sgroup_id in sgroup_ids_to_add
                    ],
                )

            if sgroup_ids_to_remove:
                await session.execute(
                    sa.delete(ScalingGroupForDomainRow).where(
                        (ScalingGroupForDomainRow.domain_id == domain_id)
                        & (ScalingGroupForDomainRow.resource_group_id.in_(sgroup_ids_to_remove))
                    ),
                )

            result = await execute_updater(session, updater)

            if result is None:
                raise DomainNotFound(f"Domain not found (id:{domain_name})")

            await session.commit()
            return result.row.to_data()

    async def _create_model_store_group(self, w: RBACWriteOps, domain_name: str) -> None:
        """
        Private method to create model-store group for a domain.
        """
        # Validate that default resource policy exists
        default_policy = await w.query(
            Querier(row_class=KeyPairResourcePolicyRow, pk_value="default")
        )
        if default_policy is None:
            raise InvalidAPIParameters(
                "Cannot create model-store group: Default resource policy does not exist"
            )

        await w.create(
            Creator(
                spec=GroupCreatorSpec(
                    name="model-store",
                    domain_name=domain_name,
                    description="Model Store",
                    resource_policy="default",
                    type=ProjectType.MODEL_STORE,
                )
            )
        )

    async def _get_domain_id(self, w: RBACWriteOps, domain_name: str) -> DomainID:
        result = await w.batch_query_in_global(
            sa.select(DomainRow.id).where(DomainRow.name == domain_name),
            BatchQuerier(pagination=NoPagination()),
        )
        if not result.rows:
            raise DomainNotFound(f"Domain not found: {domain_name}")
        return DomainID(result.rows[0].id)

    async def _domain_has_active_kernels(self, w: RBACWriteOps, domain_name: str) -> bool:
        """
        Private method to check if domain has active kernels.
        """
        result = await w.batch_query_in_global(
            sa.select(KernelRow.id).where(
                (KernelRow.domain_name == domain_name)
                & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            ),
            BatchQuerier(pagination=OffsetPagination(limit=1)),
        )
        return result.total_count > 0

    @domain_repository_resilience.apply()
    async def create_domain_node_with_permissions(
        self,
        creator: Creator[DomainRow],
        user_info: UserInfo,
        scaling_group_ids: list[ResourceGroupID] | None = None,
    ) -> DomainData:
        """
        Creates a domain node with scaling groups and permission checks.
        Validates scaling group permissions before creating.
        """

        async with self._db.begin_session() as db_session:
            if scaling_group_ids is not None:
                await self._ensure_sgroup_permission(
                    user_info, scaling_group_ids, db_session=db_session
                )
            return await self.create_domain_node(creator, scaling_group_ids)

    @domain_repository_resilience.apply()
    async def modify_domain_node_with_permissions(
        self,
        updater: Updater[DomainRow],
        user_info: UserInfo,
        sgroup_ids_to_add: set[ResourceGroupID] | None = None,
        sgroup_ids_to_remove: set[ResourceGroupID] | None = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes and permission checks.
        Validates domain and scaling group permissions.
        """
        domain_name = str(updater.pk_value)
        async with self._db.begin_session() as db_session:
            client_ctx = ClientContext(
                self._db, user_info.domain_name, user_info.id, user_info.role
            )
            domain_models = await get_domains(
                SystemScope(),
                DomainPermission.UPDATE_ATTRIBUTE,
                [domain_name],
                ctx=client_ctx,
                db_session=db_session,
            )
            if not domain_models:
                raise DomainUpdateNotAllowed(f"Not allowed to update domain (id:{domain_name})")

            if sgroup_ids_to_add is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroup_ids_to_add, db_session=db_session
                )
            if sgroup_ids_to_remove is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroup_ids_to_remove, db_session=db_session
                )

            return await self.modify_domain_node(
                updater,
                sgroup_ids_to_add,
                sgroup_ids_to_remove,
            )

    async def _ensure_sgroup_permission(
        self,
        user_info: UserInfo,
        sgroup_ids: Iterable[ResourceGroupID],
        *,
        db_session: SASession,
    ) -> None:
        """
        Private method to validate scaling group permissions.
        """
        client_ctx = ClientContext(self._db, user_info.domain_name, user_info.id, user_info.role)
        sgroup_models = await get_scaling_groups(
            SystemScope(),
            ScalingGroupPermission.ASSOCIATE_WITH_SCOPES,
            sgroup_ids=sgroup_ids,
            db_session=db_session,
            ctx=client_ctx,
        )
        not_allowed_sgroups = set(sgroup_ids) - {sg.id for sg in sgroup_models}
        if not_allowed_sgroups:
            raise InvalidDomainConfiguration(
                f"Not allowed to associate the domain with given scaling groups(s:{not_allowed_sgroups})"
            )

    # ==================== V2 Repository Methods ====================

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

    @domain_repository_resilience.apply()
    async def search_domains(self, querier: BatchQuerier) -> DomainSearchResult:
        """Search all domains with pagination and filters.

        Args:
            querier: Contains conditions, orders, and pagination.

        Returns:
            DomainSearchResult with items, total_count, and pagination flags.
        """
        return await self._db_source.search_domains(querier)

    async def search_rg_domains(
        self,
        scope: DomainOperationScope,
        querier: BatchQuerier,
    ) -> DomainSearchResult:
        """Search domains within a resource group scope.

        Args:
            scope: DomainOperationScope containing resource_group filter.
            querier: Contains additional conditions, orders, and pagination.

        Returns:
            DomainSearchResult with items, total_count, and pagination flags.
        """
        return await self._db_source.search_rg_domains(scope, querier)
