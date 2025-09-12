from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.domain.types import (
    DomainCreator,
    DomainData,
    DomainModifier,
    UserInfo,
)
from ai.backend.manager.models import groups
from ai.backend.manager.models.domain import DomainRow, domains, row_to_data
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry


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

    async def modify_domain_force(
        self, domain_name: str, modifier: DomainModifier
    ) -> Optional[DomainData]:
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
                return None

        return row_to_data(row)

    async def soft_delete_domain_force(self, domain_name: str) -> bool:
        """
        Soft deletes a domain by setting is_active to False without permission checks.
        For superadmin use only.
        """
        async with self._db.begin() as conn:
            update_query = (
                sa.update(domains).values({"is_active": False}).where(domains.c.name == domain_name)
            )
            result = await conn.execute(update_query)
            return result.rowcount > 0

    async def purge_domain_force(self, domain_name: str) -> bool:
        """
        Permanently deletes a domain without validation checks.
        For superadmin use only - bypasses all safety checks.
        """
        async with self._db.begin() as conn:
            # Force clean up kernels
            await self._delete_kernels(conn, domain_name)

            # Delete domain
            delete_query = sa.delete(domains).where(domains.c.name == domain_name)
            result = await conn.execute(delete_query)
            return result.rowcount > 0

    async def create_domain_node_force(
        self, creator: DomainCreator, scaling_groups: Optional[list[str]] = None
    ) -> DomainData:
        """
        Creates a domain node with scaling groups without permission checks.
        For superadmin use only.
        """
        async with self._db.begin_session() as session:
            data = creator.fields_to_store()
            insert_and_returning = sa.select(DomainRow).from_statement(
                sa.insert(DomainRow).values(data).returning(DomainRow)
            )
            domain_row = await session.scalar(insert_and_returning)

            if scaling_groups is not None:
                await session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": creator.name}
                        for sgroup_name in scaling_groups
                    ],
                )

            await session.commit()
            if domain_row is None:
                raise RuntimeError(f"Failed to create domain node: {creator.name}")
            assert domain_row is not None
            result = row_to_data(domain_row)
            assert result is not None
            return result

    async def modify_domain_node_force(
        self,
        domain_name: str,
        modifier_fields: dict,
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
    ) -> Optional[DomainData]:
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
            return row_to_data(domain_row) if domain_row else None

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
    ) -> Optional[DomainData]:
        """
        Modifies a domain node with scaling group changes without permission checks.
        For superadmin use only.
        """

        async def _update(db_session: SASession) -> Optional[DomainData]:
            return await self.modify_domain_node_force(
                domain_name,
                modifier_fields,
                sgroups_to_add,
                sgroups_to_remove,
            )

        async with self._db.connect() as db_conn:
            return await execute_with_txn_retry(_update, self._db.begin_session, db_conn)
