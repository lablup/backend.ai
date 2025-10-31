from typing import Iterable, Optional, cast

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
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

from ..permission_controller.role_manager import RoleManager

# Layer-specific decorator for domain repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.DOMAIN)


class DomainRepository:
    _db: ExtendedAsyncSAEngine
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

    @repository_decorator()
    async def create_domain_validated(self, creator: DomainCreator) -> DomainData:
        """
        Creates a new domain with model-store group.
        Validates domain creation permissions.
        """
        async with self._db.begin_session() as db_session:
            check_query = sa.select(DomainRow).where(DomainRow.name == creator.name)
            existing_domain = await db_session.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{creator.name}' already exists")

            domain = DomainRow.from_input(creator)
            db_session.add(domain)
            await db_session.flush()
            await db_session.refresh(domain)

            result = domain.to_data()
            await self._role_manager.create_system_role(db_session, result)

            # Create model-store group for the domain
            await self._create_model_store_group(db_session, creator.name)

            return result

    @repository_decorator()
    async def modify_domain_validated(
        self, domain_name: str, modifier: DomainModifier
    ) -> DomainData:
        """
        Modifies an existing domain.
        Validates domain modification permissions.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_stmt = (
                sa.update(DomainRow)
                .values(data)
                .where(DomainRow.name == domain_name)
                .returning(DomainRow)
            )
            query_stmt = (
                sa.select(DomainRow)
                .from_statement(update_stmt)
                .execution_options(populate_existing=True)
            )

            row = cast(Optional[DomainRow], await db_session.scalar(query_stmt))

            if row is None:
                raise DomainNotFound(f"Domain not found: {domain_name}")
            return row.to_data()

    @repository_decorator()
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

    @repository_decorator()
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

    @repository_decorator()
    async def create_domain_node_validated(
        self, creator: DomainCreator, scaling_groups: Optional[list[str]] = None
    ) -> DomainData:
        """
        Creates a domain node with scaling groups.
        Validates domain node creation permissions.
        """
        async with self._db.begin_session() as session:
            check_query = sa.select(DomainRow).where(DomainRow.name == creator.name)
            existing_domain = await session.scalar(check_query)
            if existing_domain is not None:
                raise InvalidAPIParameters(f"Domain with name '{creator.name}' already exists")

            data = creator.fields_to_store()
            insert_and_returning = sa.select(DomainRow).from_statement(
                sa.insert(DomainRow).values(data).returning(DomainRow)
            )
            domain_row: Optional[DomainRow] = await session.scalar(insert_and_returning)

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
                raise DomainDataProcessingError(
                    f"Failed to retrieve created domain node: {creator.name}"
                )
            result = domain_row.to_data()
            if result is None:
                raise DomainDataProcessingError(
                    f"Failed to convert domain node row to DomainData: {creator.name}"
                )
            return result

    @repository_decorator()
    async def modify_domain_node_validated(
        self,
        domain_name: str,
        modifier_fields: dict,
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes.
        Validates domain node modification permissions.
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

            domain_row: Optional[DomainRow] = await session.scalar(
                sa.select(DomainRow).where(DomainRow.name == domain_name)
            )

            if domain_row is None:
                raise DomainNotFound(f"Domain not found (id:{domain_name})")

            await session.commit()
            return domain_row.to_data()

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

    @repository_decorator()
    async def create_domain_node_with_permissions(
        self,
        creator: DomainCreator,
        user_info: UserInfo,
        scaling_groups: Optional[list[str]] = None,
    ) -> DomainData:
        """
        Creates a domain node with scaling groups and permission checks.
        Validates scaling group permissions before creating.
        """

        async def _insert(db_session: SASession) -> DomainData:
            if scaling_groups is not None:
                await self._ensure_sgroup_permission(
                    user_info, scaling_groups, db_session=db_session
                )
            return await self.create_domain_node_validated(creator, scaling_groups)

        async with self._db.connect() as db_conn:
            return await execute_with_txn_retry(_insert, self._db.begin_session, db_conn)

    @repository_decorator()
    async def modify_domain_node_with_permissions(
        self,
        domain_name: str,
        modifier_fields: dict,
        user_info: UserInfo,
        sgroups_to_add: Optional[set[str]] = None,
        sgroups_to_remove: Optional[set[str]] = None,
    ) -> DomainData:
        """
        Modifies a domain node with scaling group changes and permission checks.
        Validates domain and scaling group permissions.
        """

        async def _update(db_session: SASession) -> DomainData:
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
                raise ValueError(f"Not allowed to update domain (id:{domain_name})")

            if sgroups_to_add is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroups_to_add, db_session=db_session
                )
            if sgroups_to_remove is not None:
                await self._ensure_sgroup_permission(
                    user_info, sgroups_to_remove, db_session=db_session
                )

            return await self.modify_domain_node_validated(
                domain_name,
                modifier_fields,
                sgroups_to_add,
                sgroups_to_remove,
            )

        async with self._db.connect() as db_conn:
            return await execute_with_txn_retry(
                _update,
                self._db.begin_session,
                db_conn,  # type: ignore[call-overload]
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
            raise ValueError(
                f"Not allowed to associate the domain with given scaling groups(s:{not_allowed_sgroups})"
            )
