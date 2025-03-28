import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, cast

import sqlalchemy as sa
from sqlalchemy.engine import Result, Row

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SAConnection, execute_with_retry
from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.type import UserData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class UserService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        user_data = action.get_insertion_data()
        user_insert_query = sa.insert(users).values(user_data)

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            from ai.backend.manager.models.group import (
                ProjectType,
                association_groups_users,
                groups,
            )

            if result.rowcount == 0:
                return
            created_user = result.first()

            # Create a default keypair for the user.
            from ai.backend.manager.models.keypair import CreateKeyPair, keypairs

            kp_data = CreateKeyPair.prepare_new_keypair(
                action.email,
                {
                    "is_active": action.status == UserStatus.ACTIVE,
                    "is_admin": user_data["role"] in [UserRole.SUPERADMIN, UserRole.ADMIN],
                    "resource_policy": DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
                    "rate_limit": DEFAULT_KEYPAIR_RATE_LIMIT,
                },
            )
            kp_insert_query = sa.insert(keypairs).values(
                **kp_data,
                user=created_user.uuid,
            )
            await conn.execute(kp_insert_query)

            # Update user main_keypair
            main_ak = kp_data["access_key"]
            update_query = (
                sa.update(users)
                .where(users.c.uuid == created_user.uuid)
                .values(main_access_key=main_ak)
            )
            await conn.execute(update_query)

            model_store_query = sa.select([groups.c.id]).where(
                groups.c.type == ProjectType.MODEL_STORE
            )
            model_store_project = cast(
                dict[str, Any] | None, (await conn.execute(model_store_query)).first()
            )
            if model_store_project is not None:
                gids_to_join = [*action.group_ids, model_store_project["id"]]
            else:
                gids_to_join = action.group_ids

            # Add user to groups if group_ids parameter is provided.
            if gids_to_join:
                query = (
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == action.domain_name)
                    .where(groups.c.id.in_(gids_to_join))
                )
                grps = (await conn.execute(query)).all()
                if grps:
                    group_data = [
                        {"user_id": created_user.uuid, "group_id": grp.id} for grp in grps
                    ]
                    group_insert_query = sa.insert(association_groups_users).values(group_data)
                    await conn.execute(group_insert_query)

            return created_user

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                query = user_insert_query.returning(user_insert_query.table)
                result = await conn.execute(query)
                created_user = await _post_func(conn, result)
                return MutationResult(
                    success=True,
                    message="User created successfully",
                    data=created_user,
                )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        if result.success:
            return CreateUserActionResult(
                data=UserData.from_row(result.data),
                success=True,
            )
        else:
            return CreateUserActionResult(
                data=None,
                success=False,
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
