from __future__ import annotations

from typing import Iterable, Optional, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import BackendAIError, DomainNotFound, InvalidAPIParameters
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.domain.types import (
    DomainData,
    UserInfo,
)
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
    DomainUpdateNotAllowed,
    InvalidDomainConfiguration,
)
from ai.backend.manager.models import groups, users
from ai.backend.manager.models.domain import DomainRow, domains, get_domains
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.rbac import SystemScope
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import DomainPermission, ScalingGroupPermission
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow, get_scaling_groups
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec

from ..permission_controller.role_manager import RoleManager

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
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

    @domain_repository_resilience.apply()
    async def create_domain_validated(self, creator: Creator[DomainRow]) -> DomainData:
        """
        Creates a new domain with model-store group.
        Validates domain creation permissions.
        """
        spec = cast(DomainCreatorSpec, creator.spec)
        async with self._db.begin_session() as db_session:
            check_query = sa.select(DomainRow).where(DomainRow.name == spec.name)
            existing_domain = await db_session.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{spec.name}' already exists")

            creator_result = await execute_creator(db_session, creator)
            domain = creator_result.row

            data = domain.to_data()
            await self._role_manager.create_system_role(db_session, data)

            # Create model-store group for the domain
            await self._create_model_store_group(db_session, spec.name)

            return data

    @domain_repository_resilience.apply()
    async def modify_domain_validated(self, updater: Updater[DomainRow]) -> DomainData:
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
    async def soft_delete_domain_validated(self, domain_name: str) -> None:
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
    async def purge_domain_validated(self, domain_name: str) -> None:
        """
        Permanently deletes a domain after validation checks.
        Validates domain purge permissions and prerequisites.
        """
        async with self._db.begin() as conn:
            # Validate prerequisites
            if await self._domain_has_active_kernels(conn, domain_name):
                raise DomainHasActiveKernels(
                    "Domain has some active kernels. Terminate them first."
                )

            user_count = await self._get_domain_user_count(conn, domain_name)
            if user_count > 0:
                raise DomainHasUsers("There are users bound to the domain. Remove users first.")

            group_count = await self._get_domain_group_count(conn, domain_name)
            if group_count > 0:
                raise DomainHasGroups("There are groups bound to the domain. Remove groups first.")

            # Clean up kernels
            await self._delete_kernels(conn, domain_name)

            # Delete domain
            delete_query = sa.delete(domains).where(domains.c.name == domain_name)
            result = await conn.execute(delete_query)
            if result.rowcount == 0:
                raise DomainDeletionFailed(f"Failed to delete domain: {domain_name}")

    @domain_repository_resilience.apply()
    async def create_domain_node_validated(
        self, creator: Creator[DomainRow], scaling_groups: Optional[list[str]] = None
    ) -> DomainData:
        """
        Creates a domain node with scaling groups.
        Validates domain node creation permissions.
        """
        spec = cast(DomainCreatorSpec, creator.spec)
        async with self._db.begin_session() as session:
            check_query = sa.select(DomainRow).where(DomainRow.name == spec.name)
            existing_domain = await session.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{spec.name}' already exists")

            creator_result = await execute_creator(session, creator)
            domain_row = creator_result.row

            if scaling_groups is not None:
                await session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": spec.name}
                        for sgroup_name in scaling_groups
                    ],
                )

            await session.commit()
            return domain_row.to_data()

    @domain_repository_resilience.apply()
    async def modify_domain_node_validated(
        self,
        updater: Updater[DomainRow],
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes.
        Validates domain node modification permissions.
        """
        domain_name = str(updater.pk_value)
        async with self._db.begin_session() as session:
            if sgroups_to_add is not None:
                await session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": domain_name}
                        for sgroup_name in sgroups_to_add
                    ],
                )

            if sgroups_to_remove is not None:
                await session.execute(
                    sa.delete(ScalingGroupForDomainRow).where(
                        (ScalingGroupForDomainRow.domain == domain_name)
                        & (ScalingGroupForDomainRow.scaling_group.in_(sgroups_to_remove))
                    ),
                )

            result = await execute_updater(session, updater)

            if result is None:
                raise DomainNotFound(f"Domain not found (id:{domain_name})")

            await session.commit()
            return result.row.to_data()

    async def _create_model_store_group(self, db_session: SASession, domain_name: str) -> None:
        """
        Private method to create model-store group for a domain.
        """
        # Validate that default resource policy exists
        policy_exists = await db_session.scalar(
            sa.select(sa.exists().where(keypair_resource_policies.c.name == "default"))
        )
        if not policy_exists:
            raise InvalidAPIParameters(
                "Cannot create model-store group: Default resource policy does not exist"
            )

        model_store_insert_query = sa.insert(groups).values({
            "name": "model-store",
            "description": "Model Store",
            "is_active": True,
            "domain_name": domain_name,
            "total_resource_slots": {},
            "allowed_vfolder_hosts": {},
            "integration_id": None,
            "resource_policy": "default",
            "type": ProjectType.MODEL_STORE,
        })
        await db_session.execute(model_store_insert_query)

    async def _delete_kernels(self, conn: SAConnection, domain_name: str) -> int:
        """
        Private method to delete all kernels for a domain.
        """
        delete_query = sa.delete(kernels).where(kernels.c.domain_name == domain_name)
        result = await conn.execute(delete_query)
        return result.rowcount

    async def _domain_has_active_kernels(self, conn: SAConnection, domain_name: str) -> bool:
        """
        Private method to check if domain has active kernels.
        """
        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.domain_name == domain_name)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await conn.scalar(query)
        return active_kernel_count > 0

    async def _get_domain_user_count(self, conn: SAConnection, domain_name: str) -> int:
        """
        Private method to get user count for a domain.
        """
        query = sa.select([sa.func.count()]).where(users.c.domain_name == domain_name)
        return await conn.scalar(query)

    async def _get_domain_group_count(self, conn: SAConnection, domain_name: str) -> int:
        """
        Private method to get group count for a domain.
        """
        query = sa.select([sa.func.count()]).where(groups.c.domain_name == domain_name)
        return await conn.scalar(query)

    @domain_repository_resilience.apply()
    async def create_domain_node_with_permissions(
        self,
        creator: Creator[DomainRow],
        user_info: UserInfo,
        scaling_groups: Optional[list[str]] = None,
    ) -> DomainData:
        """
        Creates a domain node with scaling groups and permission checks.
        Validates scaling group permissions before creating.
        """

        async with self._db.begin_session() as db_session:
            if scaling_groups is not None:
                await self._ensure_sgroup_permission(
                    user_info, scaling_groups, db_session=db_session
                )
            return await self.create_domain_node_validated(creator, scaling_groups)

    @domain_repository_resilience.apply()
    async def modify_domain_node_with_permissions(
        self,
        updater: Updater[DomainRow],
        user_info: UserInfo,
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
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

            if sgroups_to_add is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroups_to_add, db_session=db_session
                )
            if sgroups_to_remove is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroups_to_remove, db_session=db_session
                )

            return await self.modify_domain_node_validated(
                updater,
                sgroups_to_add,
                sgroups_to_remove,
            )

    async def _ensure_sgroup_permission(
        self, user_info: UserInfo, sgroup_names: Iterable[str], *, db_session: SASession
    ) -> None:
        """
        Private method to validate scaling group permissions.
        """
        client_ctx = ClientContext(self._db, user_info.domain_name, user_info.id, user_info.role)
        sgroup_models = await get_scaling_groups(
            SystemScope(),
            ScalingGroupPermission.ASSOCIATE_WITH_SCOPES,
            sgroup_names,
            db_session=db_session,
            ctx=client_ctx,
        )
        not_allowed_sgroups = set(sgroup_names) - set([sg.name for sg in sgroup_models])
        if not_allowed_sgroups:
            raise InvalidDomainConfiguration(
                f"Not allowed to associate the domain with given scaling groups(s:{not_allowed_sgroups})"
            )
