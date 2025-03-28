import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, cast

import sqlalchemy as sa
from sqlalchemy.engine import Result, Row
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload
from sqlalchemy.sql.expression import bindparam

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SAConnection, execute_with_retry
from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.users.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
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

    async def modify_user(self, action: ModifyUserAction) -> ModifyUserActionResult:
        data = action.get_modified_data()
        email = action.email

        if not data and action.group_ids is None:
            return ModifyUserActionResult(
                success=False,
                message="No data to update",
            )

        main_access_key: str | None = data.get("main_access_key")
        user_update_data: dict[str, Any] = {}
        prev_domain_name: str
        prev_role: UserRole

        async def _pre_func(conn: SAConnection) -> None:
            nonlocal user_update_data, prev_domain_name, prev_role, main_access_key
            result = await conn.execute(
                sa.select([users.c.domain_name, users.c.role, users.c.status])
                .select_from(users)
                .where(users.c.email == email),
            )
            row = result.first()
            prev_domain_name = row.domain_name
            prev_role = row.role
            user_update_data = data.copy()
            if "status" in data and row.status != data["status"]:
                user_update_data["status_info"] = (
                    "admin-requested"  # user mutation is only for admin
                )
            if main_access_key is not None:
                db_session = SASession(conn)
                keypair_query = (
                    sa.select(KeyPairRow)
                    .where(KeyPairRow.access_key == main_access_key)
                    .options(
                        noload("*"),
                        joinedload(KeyPairRow.user_row).options(load_only(UserRow.email)),
                    )
                )
                keypair_row: KeyPairRow | None = (await db_session.scalars(keypair_query)).first()
                if keypair_row is None:
                    raise RuntimeError("Cannot set non-existing access key as the main access key.")
                if keypair_row.user_row.email != email:
                    raise RuntimeError(
                        "Cannot set another user's access key as the main access key."
                    )
                await conn.execute(
                    sa.update(users)
                    .where(users.c.email == email)
                    .values(main_access_key=main_access_key)
                )

        update_query = lambda: (  # uses lambda because user_update_data is modified in _pre_func()
            sa.update(users).values(user_update_data).where(users.c.email == email)
        )

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            nonlocal prev_domain_name, prev_role
            updated_user = result.first()
            if "role" in data and data["role"] != prev_role:
                from ai.backend.manager.models import keypairs

                result = await conn.execute(
                    sa.select([
                        keypairs.c.user,
                        keypairs.c.is_active,
                        keypairs.c.is_admin,
                        keypairs.c.access_key,
                    ])
                    .select_from(keypairs)
                    .where(keypairs.c.user == updated_user.uuid)
                    .order_by(sa.desc(keypairs.c.is_admin))
                    .order_by(sa.desc(keypairs.c.is_active)),
                )
                if data["role"] in [UserRole.SUPERADMIN, UserRole.ADMIN]:
                    # User's becomes admin. Set the keypair as active admin.
                    # TODO: Should we update the role of all users related to keypair?
                    kp = result.first()
                    kp_data = dict()
                    if not kp.is_admin:
                        kp_data["is_admin"] = True
                    if not kp.is_active:
                        kp_data["is_active"] = True
                    if kp_data:
                        await conn.execute(
                            sa.update(keypairs)
                            .values(kp_data)
                            .where(keypairs.c.user == updated_user.uuid),
                        )
                else:
                    # User becomes non-admin. Make the keypair non-admin as well.
                    # If there are multiple admin keypairs, inactivate them.
                    # TODO: Should elaborate keypair inactivation policy.
                    rows = result.fetchall()
                    kp_updates = []
                    for idx, row in enumerate(rows):
                        kp_data = {
                            "b_access_key": row.access_key,
                            "is_admin": row.is_admin,
                            "is_active": row.is_active,
                        }
                        if idx == 0:
                            kp_data["is_admin"] = False
                            kp_updates.append(kp_data)
                            continue
                        if row.is_admin and row.is_active:
                            kp_data["is_active"] = False
                            kp_updates.append(kp_data)
                    if kp_updates:
                        await conn.execute(
                            sa.update(keypairs)
                            .values({
                                "is_admin": bindparam("is_admin"),
                                "is_active": bindparam("is_active"),
                            })
                            .where(keypairs.c.access_key == bindparam("b_access_key")),
                            kp_updates,
                        )

            # If domain is changed and no group is associated, clear previous domain's group.
            if prev_domain_name != updated_user.domain_name and not action.group_ids:
                from ai.backend.manager.models import association_groups_users, groups

                await conn.execute(
                    sa.delete(association_groups_users).where(
                        association_groups_users.c.user_id == updated_user.uuid
                    ),
                )

            # Update user's group if group_ids parameter is provided.
            if action.group_ids and updated_user is not None:
                from ai.backend.manager.models import association_groups_users, groups  # noqa

                # Clear previous groups associated with the user.
                await conn.execute(
                    sa.delete(association_groups_users).where(
                        association_groups_users.c.user_id == updated_user.uuid
                    ),
                )
                # Add user to new groups.
                result = await conn.execute(
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == updated_user.domain_name)
                    .where(groups.c.id.in_(action.group_ids)),
                )
                grps = result.fetchall()
                if grps:
                    values = [{"user_id": updated_user.uuid, "group_id": grp.id} for grp in grps]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )

            return updated_user

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                await _pre_func(conn)
                query = update_query().returning(update_query().table)
                result = await conn.execute(query)
                updated_user = await _post_func(conn, result)

            return MutationResult(
                success=True,
                message="User modified successfully",
                data=updated_user,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return ModifyUserActionResult(
            success=result.success,
            data=UserData.from_row(result.data),
        )

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        async def _pre_func(conn: SAConnection) -> None:
            # Make all user keypairs inactive.
            from ai.backend.manager.models import keypairs

            await conn.execute(
                sa.update(keypairs)
                .values(is_active=False)
                .where(keypairs.c.user_id == action.email),
            )

        update_query = (
            sa.update(users)
            .values(status=UserStatus.DELETED, status_info="admin-requested")
            .where(users.c.email == action.email)
        )

        async def _do_mutate() -> MutationResult:
            async with self._db.begin() as conn:
                await _pre_func(conn)
                await conn.execute(update_query)

            return MutationResult(
                success=True,
                message="User deleted successfully",
                data=None,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        return DeleteUserActionResult(
            success=result.success,
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
