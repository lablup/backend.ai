from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.domain.types import (
    DomainCreator,
    DomainData,
    DomainModifier,
    UserInfo,
)
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.resource import (
    DomainDataProcessingError,
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
    DomainNotFound,
)
from ai.backend.manager.models import groups
from ai.backend.manager.models.domain import DomainRow, domains, row_to_data
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

# Layer-specific decorator for admin domain repository
admin_repository_decorator = create_layer_aware_repository_decorator(LayerType.DOMAIN)


class AdminDomainRepository:
    """
    Repository for admin-specific domain operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_domain_force(self, creator: DomainCreator) -> DomainData:
        """
        Creates a new domain with model-store group without permission checks.
        For superadmin use only.
        """
        async with self._db.begin() as conn:
            check_query = sa.select(DomainRow).where(DomainRow.name == creator.name)
            existing_domain = await conn.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{creator.name}' already exists")

            data = creator.fields_to_store()
            insert_query = sa.insert(domains).values(data).returning(domains)
            result = await conn.execute(insert_query)
            row = result.first()

            # Create model-store group for the domain
            await self._create_model_store_group(conn, creator.name)

            if result.rowcount != 1 or row is None:
                raise RuntimeError(f"No domain created. rowcount: {result.rowcount}, data: {data}")

        assert row is not None
        result = row_to_data(row)
        assert result is not None
        return result

    @admin_repository_decorator()
    async def modify_domain_force(self, domain_name: str, modifier: DomainModifier) -> DomainData:
        """
        Modifies an existing domain without permission checks.
        For superadmin use only.
        """
        async with self._db.begin() as conn:
            data = modifier.fields_to_update()
            update_query = (
                sa.update(domains)
                .values(data)
                .where(domains.c.name == domain_name)
                .returning(domains)
            )
            result = await conn.execute(update_query)
            row = result.first()

            if result.rowcount == 0:
                raise DomainNotFound(f"Domain not found: {domain_name}")
            return row_to_data(row)

    @admin_repository_decorator()
    async def soft_delete_domain_force(self, domain_name: str) -> None:
        """
        Soft deletes a domain by setting is_active to False without permission checks.
        For superadmin use only.
        """
        async with self._db.begin() as conn:
            update_query = (
                sa.update(domains).values({"is_active": False}).where(domains.c.name == domain_name)
            )
            result = await conn.execute(update_query)
            if result.rowcount == 0:
                raise DomainNotFound(f"Domain not found: {domain_name}")

    @admin_repository_decorator()
    async def purge_domain_force(self, domain_name: str) -> None:
        """
        Permanently deletes a domain without validation checks.
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

    async def create_domain_node_force(
        self, creator: DomainCreator, scaling_groups: Optional[list[str]] = None
    ) -> DomainData:
        """
        Creates a domain node with scaling groups without permission checks.
        For superadmin use only.
        """
        async with self._db.begin_session() as session:
            data = creator.fields_to_store()
            check_query = sa.select(DomainRow).where(DomainRow.name == creator.name)
            existing_domain = await session.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{creator.name}' already exists")

            insert_and_returning = sa.select(DomainRow).from_statement(
                sa.insert(DomainRow).values(data).returning(DomainRow)
            )
            domain_row = await session.scalar(insert_and_returning)
            if domain_row is None:
                raise DomainDataProcessingError(f"Failed to create domain node: {creator.name}")

            if scaling_groups is not None:
                await session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": creator.name}
                        for sgroup_name in scaling_groups
                    ],
                )

            await session.commit()
            result = row_to_data(domain_row)
            assert result is not None
            return result

    async def _create_model_store_group(self, conn: SAConnection, domain_name: str) -> None:
        """
        Private method to create model-store group for a domain.
        """
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
        await conn.execute(model_store_insert_query)

    async def _delete_kernels(self, conn: SAConnection, domain_name: str) -> int:
        """
        Private method to delete all kernels for a domain.
        """
        delete_query = sa.delete(kernels).where(kernels.c.domain_name == domain_name)
        result = await conn.execute(delete_query)
        return result.rowcount

    async def create_domain_node_with_permissions_force(
        self,
        creator: DomainCreator,
        user_info: UserInfo,
        scaling_groups: Optional[list[str]] = None,
    ) -> DomainData:
        """
        Creates a domain node with scaling groups without permission checks.
        For superadmin use only.
        """

        async def _insert(db_session: SASession) -> DomainData:
            return await self.create_domain_node_force(creator, scaling_groups)

        async with self._db.connect() as db_conn:
            return await execute_with_txn_retry(_insert, self._db.begin_session, db_conn)

    async def modify_domain_node_with_permissions_force(
        self,
        domain_name: str,
        modifier_fields: dict,
        user_info: UserInfo,
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes without permission checks.
        For superadmin use only.
        """
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

            update_stmt = (
                sa.update(DomainRow)
                .where(DomainRow.name == domain_name)
                .values(modifier_fields)
                .returning(DomainRow)
            )
            await session.execute(update_stmt)

            domain_row = await session.scalar(
                sa.select(DomainRow).where(DomainRow.name == domain_name)
            )

            await session.commit()
            if domain_row is None:
                raise DomainNotFound(f"Domain not found (id:{domain_name})")
            return row_to_data(domain_row)
