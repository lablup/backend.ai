import asyncio
import logging
from typing import Awaitable, Callable, Iterable, Optional, TypeVar, cast

import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.domain import Domain, DomainRow, get_domains
from ai.backend.manager.models.rbac import SystemScope
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import DomainPermission, ScalingGroupPermission
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow, get_scaling_groups
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    execute_with_txn_retry,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.domain.actions import (
    CreateDomainAction,
    CreateDomainActionResult,
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.base import UserInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
ResultType = TypeVar("ResultType")


class DomainService:
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, db: ExtendedAsyncSAEngine, registry: AgentRegistry) -> None:
        self._db = db
        self._registry = registry

    async def create_domain(self, action: CreateDomainAction) -> CreateDomainActionResult:
        data = action.get_insert_data()
        base_query = sa.insert(DomainRow).values(data)

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            from ai.backend.manager.models.group import GroupRow, ProjectType

            model_store_insert_query = sa.insert(GroupRow).values({
                "name": "model-store",
                "description": "Model Store",
                "is_active": True,
                "domain_name": action.domain_name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": None,
                "resource_policy": "default",
                "type": ProjectType.MODEL_STORE,
            })
            await conn.execute(model_store_insert_query)

        async def _do_mutate() -> tuple[bool, str, Optional[Row]]:
            async with self._db.begin() as conn:
                query = base_query.returning(base_query.table)
                result = await conn.execute(query)
                row = result.first()
                await _post_func(conn, result)
                if result.rowcount > 0:
                    return True, "domain creation succeed", row
                else:
                    return False, f"no matching {Domain.__name__.lower()}", None

        sucess, message, row = await self._db_mutation_wrapper(_do_mutate)
        status = "success" if sucess else "failed"

        return CreateDomainActionResult(domain_row=row, status=status, description=message)

    async def create_domain_node(
        self, action: CreateDomainNodeAction
    ) -> CreateDomainNodeActionResult:
        if hasattr(action, "scaling_groups") and action.scaling_groups is not None:
            scaling_groups = cast(list[str], action.scaling_groups)
        else:
            scaling_groups = None

        async def _insert(db_session: AsyncSession) -> DomainRow:
            if scaling_groups is not None:
                await self._ensure_sgroup_permission(
                    action.user_info, scaling_groups, db_session=db_session
                )
            _insert_and_returning = sa.select(DomainRow).from_statement(
                sa.insert(DomainRow).values(**action).returning(DomainRow)
            )
            domain_row = await db_session.scalar(_insert_and_returning)
            if scaling_groups is not None:
                await db_session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": action.name}
                        for sgroup_name in scaling_groups
                    ],
                )
            return domain_row

        async with self._db.connect() as db_conn:
            try:
                domain_row = await execute_with_txn_retry(_insert, self._db.begin_session, db_conn)
            except sa.exc.IntegrityError as e:
                raise ValueError(
                    f"Cannot create the domain with given arguments. (arg:{action}, e:{str(e)})"
                )

        return CreateDomainNodeActionResult(
            domain_row=domain_row, status="success", description=f"domain {action.name} created"
        )

    async def modify_domain_node(
        self, action: ModifyDomainNodeAction
    ) -> ModifyDomainNodeActionResult:
        domain_name = action.domain_name

        if hasattr(action, "sgroups_to_add") and action.sgroups_to_add is not None:
            sgroups_to_add = set(action.sgroups_to_add)
        else:
            sgroups_to_add = None

        if hasattr(action, "sgroups_to_remove") and action.sgroups_to_remove is not None:
            sgroups_to_remove = set(action.sgroups_to_remove)
        else:
            sgroups_to_remove = None

        if sgroups_to_add is not None and sgroups_to_remove is not None:
            if union := sgroups_to_add & sgroups_to_remove:
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

            if sgroups_to_add is not None:
                await self._ensure_sgroup_permission(
                    action.user_info, sgroups_to_add, db_session=db_session
                )
                await db_session.execute(
                    sa.insert(ScalingGroupForDomainRow),
                    [
                        {"scaling_group": sgroup_name, "domain": domain_name}
                        for sgroup_name in sgroups_to_add
                    ],
                )
            if sgroups_to_remove is not None:
                await self._ensure_sgroup_permission(
                    action.user_info, sgroups_to_remove, db_session=db_session
                )
                await db_session.execute(
                    sa.delete(ScalingGroupForDomainRow).where(
                        (ScalingGroupForDomainRow.domain == domain_name)
                        & (ScalingGroupForDomainRow.scaling_group.in_(sgroups_to_remove))
                    ),
                )
            _update_stmt = (
                sa.update(DomainRow)
                .where(DomainRow.name == domain_name)
                .values(action)
                .returning(DomainRow)
            )
            _stmt = sa.select(DomainRow).from_statement(_update_stmt)

            return await db_session.scalar(_stmt)

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
            domain_row=domain_row, status="success", description=f"domain {domain_name} modified"
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
        self, _do_mutate: Callable[[], Awaitable[ResultType]]
    ) -> tuple[bool, str, Optional[Row]]:
        try:
            result = await execute_with_retry(_do_mutate)
            return True, "success", result
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return False, f"integrity error: {e}", None
        except sa.exc.StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return False, str(orig_exc), None
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            log.exception("db_mutation_wrapper(): other error")
            return False, f"unexpected error: {e}", None
