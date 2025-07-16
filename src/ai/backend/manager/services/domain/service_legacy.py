import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Optional

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.logging.utils import BraceStyleAdapter
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
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow, get_scaling_groups
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    execute_with_txn_retry,
)
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import (
    DeleteDomainAction,
    DeleteDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain import (
    ModifyDomainAction,
    ModifyDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.types import DomainData, UserInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class DomainService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_domain(self, action: CreateDomainAction) -> CreateDomainActionResult:
        data = action.creator.fields_to_store()
        base_query = sa.insert(domains).values(data)

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            model_store_insert_query = sa.insert(groups).values({
                "name": "model-store",
                "description": "Model Store",
                "is_active": True,
                "domain_name": action.creator.name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": None,
                "resource_policy": "default",
                "type": ProjectType.MODEL_STORE,
            })
            await conn.execute(model_store_insert_query)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = base_query.returning(base_query.table)
                result = await conn.execute(query)
                row = result.first()
                await _post_func(conn, result)
                if result.rowcount != 1:
                    raise RuntimeError(
                        f"No domain created. rowcount: {result.rowcount}, data: {data}"
                    )
                return MutationResult(success=True, message="domain creation succeed", data=row)

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return CreateDomainActionResult(
            domain_data=DomainData.from_row(res.data),
            success=res.success,
            description=res.message,
        )

    async def modify_domain(self, action: ModifyDomainAction) -> ModifyDomainActionResult:
        data = action.get_modified_fields()
        base_query = sa.update(domains).values(data).where(domains.c.name == action.domain_name)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = base_query.returning(base_query.table)
                result = await conn.execute(query)
                row = result.first()
                if result.rowcount > 0:
                    return MutationResult(
                        success=True, message="domain modification succeed", data=row
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.modifier.name}", data=None
                    )

        res = await self._db_mutation_wrapper(_do_mutate)

        return ModifyDomainActionResult(
            domain_data=DomainData.from_row(res.data),
            success=res.success,
            description=res.message,
        )

    async def delete_domain(self, action: DeleteDomainAction) -> DeleteDomainActionResult:
        base_query = (
            sa.update(domains).values({"is_active": False}).where(domains.c.name == action.name)
        )

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                result = await conn.execute(base_query)
                # TODO: Raise Error if rowcount is 0
                if result.rowcount > 0:
                    return MutationResult(
                        success=True,
                        message=f"domain {action.name} deleted successfully",
                        data=None,
                    )
                else:
                    return MutationResult(
                        success=False, message=f"no matching {action.name}", data=None
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return DeleteDomainActionResult(success=res.success, description=res.message)

    async def purge_domain(self, action: PurgeDomainAction) -> PurgeDomainActionResult:
        name = action.name

        async def _pre_func(conn: SAConnection) -> None:
            if await self._domain_has_active_kernels(conn, name):
                raise RuntimeError("Domain has some active kernels. Terminate them first.")
            query = sa.select([sa.func.count()]).where(users.c.domain_name == name)
            user_count = await conn.scalar(query)
            if user_count > 0:
                raise RuntimeError("There are users bound to the domain. Remove users first.")
            query = sa.select([sa.func.count()]).where(groups.c.domain_name == name)
            group_count = await conn.scalar(query)
            if group_count > 0:
                raise RuntimeError("There are groups bound to the domain. Remove groups first.")

            await self._delete_kernels(conn, name)

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                await _pre_func(conn)
                delete_query = sa.delete(domains).where(domains.c.name == name)
                result = await conn.execute(delete_query)
                # TODO: Raise Error if rowcount is 0
                if result.rowcount > 0:
                    return MutationResult(
                        success=True, message=f"domain {name} purged successfully", data=None
                    )
                else:
                    return MutationResult(
                        success=False,
                        message=f"no matching {name} domain to purge",
                        data=None,
                    )

        res: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return PurgeDomainActionResult(success=res.success, description=res.message)

    async def _delete_kernels(self, conn: SAConnection, domain_name: str) -> int:
        delete_query = sa.delete(kernels).where(kernels.c.domain_name == domain_name)
        result = await conn.execute(delete_query)
        if result.rowcount > 0:
            log.info('deleted {0} domain"s kernels ({1})', result.rowcount, domain_name)
        return result.rowcount

    async def _domain_has_active_kernels(self, conn: SAConnection, domain_name: str) -> bool:
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

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        scaling_groups = action.scaling_groups

        async def _insert(db_session: AsyncSession) -> DomainRow:
            if scaling_groups is not None:
                await self._ensure_sgroup_permission(
                    action.user_info, scaling_groups, db_session=db_session
                )
            data = action.creator.fields_to_store()
            insert_and_returning = sa.select(DomainRow).from_statement(
                sa.insert(DomainRow).values(data).returning(DomainRow)
            )
            domain_row = await db_session.scalar(insert_and_returning)
            if scaling_groups is not None:
                await db_session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": action.creator.name}
                        for sgroup_name in scaling_groups
                    ],
                )
            return domain_row

        async with self._db.connect() as db_conn:
            try:
                domain_row: DomainRow = await execute_with_txn_retry(
                    _insert, self._db.begin_session, db_conn
                )
            except sa.exc.IntegrityError as e:
                raise ValueError(
                    f"Cannot create the domain with given arguments. (arg:{action}, e:{str(e)})"
                )

        return CreateDomainNodeActionResult(
            domain_data=DomainData.from_row(domain_row),
            success=True,
            description=f"domain {action.creator.name} created",
        )

    async def modify_domain_node(
        self, action: ModifyDomainNodeAction
    ) -> ModifyDomainNodeActionResult:
        domain_name = action.name

        if action.sgroups_to_add is not None and action.sgroups_to_remove is not None:
            if union := action.sgroups_to_add | action.sgroups_to_remove:
                raise ValueError(
                    "Should be no scaling group names included in both `sgroups_to_add` and `sgroups_to_remove` "
                    f"(sg:{union})."
                )

        async def _update(db_session: AsyncSession) -> Optional[DomainRow]:
            user_info = action.user_info
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

            if action.sgroups_to_add is not None:
                await self._ensure_sgroup_permission(
                    user_info, action.sgroups_to_add, db_session=db_session
                )
                await db_session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": domain_name}
                        for sgroup_name in action.sgroups_to_add
                    ],
                )
            if action.sgroups_to_remove is not None:
                await self._ensure_sgroup_permission(
                    user_info, action.sgroups_to_remove, db_session=db_session
                )
                await db_session.execute(
                    sa.delete(ScalingGroupForDomainRow).where(
                        (ScalingGroupForDomainRow.domain == domain_name)
                        & (ScalingGroupForDomainRow.scaling_group.in_(action.sgroups_to_remove))
                    ),
                )
            _update_stmt = (
                sa.update(DomainRow)
                .where(DomainRow.name == domain_name)
                .values(action.modifier.fields_to_update())
                .returning(DomainRow)
            )
            await db_session.execute(_update_stmt)

            return await db_session.scalar(
                sa.select(DomainRow).where(DomainRow.name == domain_name)
            )

        async with self._db.connect() as db_conn:
            try:
                domain_row = await execute_with_txn_retry(_update, self._db.begin_session, db_conn)
            except sa.exc.IntegrityError as e:
                raise ValueError(
                    f"Cannot modify the domain with given arguments. (arg:{action}, e:{str(e)})"
                )
        if domain_row is None:
            raise ValueError(f"Domain not found (id:{domain_name})")

        return ModifyDomainNodeActionResult(
            domain_data=DomainData.from_row(domain_row),
            success=True,
            description=f"domain {domain_name} modified",
        )

    async def _ensure_sgroup_permission(
        self, user_info: UserInfo, sgroup_names: Iterable[str], *, db_session: AsyncSession
    ) -> None:
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

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except sa.exc.StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            log.exception("db_mutation_wrapper(): other error")
            raise
