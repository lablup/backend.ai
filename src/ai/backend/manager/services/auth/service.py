import logging
from collections import ChainMap
from datetime import datetime
from typing import Mapping, Optional, cast

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.engine.row import Row

from ai.backend.common.dto.manager.auth.field import AuthTokenType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.plugin.hook import ALL_COMPLETED, FIRST_COMPLETED, PASSED, HookPluginContext
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.errors.exceptions import (
    AuthorizationFailed,
    GenericBadRequest,
    GenericForbidden,
    InternalServerError,
    ObjectNotFound,
    PasswordExpired,
    RejectedByHook,
    UserNotFound,
)
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.keypair import (
    generate_keypair,
    generate_ssh_keypair,
    keypairs,
    validate_ssh_keypair,
)
from ai.backend.manager.models.user import (
    INACTIVE_USER_STATUSES,
    UserRole,
    UserRow,
    UserStatus,
    check_credential,
    compare_to_hashed_password,
    users,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.services.auth.actions.authorize import (
    AuthorizeAction,
    AuthorizeActionResult,
)
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairAction,
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction, GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import (
    GetSSHKeypairAction,
    GetSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.signout import SignoutAction, SignoutActionResult
from ai.backend.manager.services.auth.actions.signup import SignupAction, SignupActionResult
from ai.backend.manager.services.auth.actions.update_full_name import (
    UpdateFullNameAction,
    UpdateFullNameActionResult,
)
from ai.backend.manager.services.auth.actions.update_password import (
    UpdatePasswordAction,
    UpdatePasswordActionResult,
)
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import (
    UploadSSHKeypairAction,
    UploadSSHKeypairActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuthService:
    _db: ExtendedAsyncSAEngine
    _hook_plugin_ctx: HookPluginContext

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        hook_plugin_ctx: HookPluginContext,
    ) -> None:
        self._db = db
        self._hook_plugin_ctx = hook_plugin_ctx

    async def get_role(self, action: GetRoleAction) -> GetRoleActionResult:
        group_role = None
        if action.group_id is not None:
            query = (
                # TODO: per-group role is not yet implemented.
                sa.select([association_groups_users.c.group_id])
                .select_from(association_groups_users)
                .where(
                    (association_groups_users.c.group_id == action.group_id)
                    & (association_groups_users.c.user_id == action.user_id),
                )
            )
            async with self._db.begin() as conn:
                result = await conn.execute(query)
                row = result.first()
                if row is None:
                    raise ObjectNotFound(
                        extra_msg="No such project or you are not the member of it.",
                        object_name="project (user group)",
                    )
            group_role = "user"

        return GetRoleActionResult(
            global_role="superadmin" if action.is_superadmin else "user",
            domain_role="admin" if action.is_admin else "user",
            group_role=group_role,
        )

    async def authorize(self, action: AuthorizeAction) -> AuthorizeActionResult:
        if action.type != AuthTokenType.KEYPAIR:
            # other types are not implemented yet.
            raise InvalidAPIParameters("Unsupported authorization type")

        params = action.hook_params
        hook_result = await self._hook_plugin_ctx.dispatch(
            "AUTHORIZE",
            (action.request, params),
            return_when=FIRST_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)
        elif hook_result.result:
            # Passed one of AUTHORIZED hook
            user = hook_result.result
        else:
            # No AUTHORIZE hook is defined (proceed with normal login)
            user = await check_credential(
                db=self._db,
                domain=action.domain_name,
                email=action.email,
                password=action.password,
            )
        if user is None:
            raise AuthorizationFailed("User credential mismatch.")
        if user["status"] == UserStatus.BEFORE_VERIFICATION:
            raise AuthorizationFailed("This account needs email verification.")
        if user["status"] in INACTIVE_USER_STATUSES:
            raise AuthorizationFailed("User credential mismatch.")
        await self._check_password_age(user, action.auth_config)
        async with self._db.begin_session() as db_session:
            user_row = await UserRow.query_user_by_uuid(user["uuid"], db_session)
            if user_row is None:
                raise UserNotFound(extra_data=user["uuid"])
            main_keypair_row = user_row.get_main_keypair_row()
        if main_keypair_row is None:
            raise AuthorizationFailed("No API keypairs found.")
        # [Hooking point for POST_AUTHORIZE]
        # The hook handlers should accept a tuple of the request, user, and keypair objects.
        hook_result = await self._hook_plugin_ctx.dispatch(
            "POST_AUTHORIZE",
            (action.request, params, user, main_keypair_row.mapping),
            return_when=FIRST_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)
        if hook_result.result is not None and isinstance(hook_result.result, web.StreamResponse):
            return AuthorizeActionResult(
                stream_response=hook_result.result,
                authorization_result=None,
            )

        return AuthorizeActionResult(
            stream_response=None,
            authorization_result=AuthorizationResult(
                access_key=main_keypair_row.access_key,
                secret_key=main_keypair_row.secret_key,
                user_id=user["uuid"],
                role=user["role"],
                status=user["status"],
            ),
        )

    async def signup(self, action: SignupAction) -> SignupActionResult:
        params = action.hook_params
        hook_result = await self._hook_plugin_ctx.dispatch(
            "PRE_SIGNUP",
            (params,),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)
        else:
            # Merge the hook results as a single map.
            user_data_overriden = ChainMap(*cast(Mapping, hook_result.result))

        # [Hooking point for VERIFY_PASSWORD_FORMAT with the ALL_COMPLETED requirement]
        # The hook handlers should accept the request and whole ``params` dict.
        # They should return None if the validation is successful and raise the
        # Reject error otherwise.
        hook_result = await self._hook_plugin_ctx.dispatch(
            "VERIFY_PASSWORD_FORMAT",
            (action.request, params),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            hook_result.reason = hook_result.reason or "invalid password format"
            raise RejectedByHook.from_hook_result(hook_result)

        async with self._db.begin() as conn:
            # Check if email already exists.
            query = sa.select([users]).select_from(users).where((users.c.email == action.email))
            result = await conn.execute(query)
            row = result.first()
            if row is not None:
                raise GenericBadRequest("Email already exists")

            # Create a user.
            data = {
                "domain_name": action.domain_name,
                "username": action.username if action.username is not None else action.email,
                "email": action.email,
                "password": action.password,
                "need_password_change": False,
                "full_name": action.full_name if action.full_name is not None else "",
                "description": action.description if action.description is not None else "",
                "status": UserStatus.ACTIVE,
                "status_info": "user-signup",
                "role": UserRole.USER,
                "integration_id": None,
                "resource_policy": "default",
                "sudo_session_enabled": False,
            }
            if user_data_overriden:
                for key, val in user_data_overriden.items():
                    if (
                        key in data  # take only valid fields
                        and key != "resource_policy"  # resource_policy in user_data is for keypair
                    ):
                        data[key] = val
            query = users.insert().values(data)
            result = await conn.execute(query)
            if result.rowcount > 0:
                checkq = users.select().where(users.c.email == action.email)
                result = await conn.execute(checkq)
                user = result.first()
                # Create user's first access_key and secret_key.
                ak, sk = generate_keypair()
                resource_policy = user_data_overriden.get("resource_policy", "default")
                kp_data = {
                    "user_id": action.email,
                    "access_key": ak,
                    "secret_key": sk,
                    "is_active": True if data.get("status") == UserStatus.ACTIVE else False,
                    "is_admin": False,
                    "resource_policy": resource_policy,
                    "rate_limit": 1000,
                    "num_queries": 0,
                    "user": user.uuid,
                }
                query = keypairs.insert().values(kp_data)
                await conn.execute(query)

                # Add user to the default group.
                group_name = user_data_overriden.get("group", "default")
                query = (
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == action.domain_name)
                    .where(groups.c.name == group_name)
                )
                result = await conn.execute(query)
                grp = result.first()
                if grp is not None:
                    values = [{"user_id": user.uuid, "group_id": grp.id}]
                    query = association_groups_users.insert().values(values)
                    await conn.execute(query)
            else:
                raise InternalServerError("Error creating user account")

        # [Hooking point for POST_SIGNUP as one-way notification]
        # The hook handlers should accept a tuple of the user email,
        # the new user's UUID, and a dict with initial user's preferences.
        initial_user_prefs = {
            "lang": action.request.headers.get("Accept-Language", "en-us").split(",")[0].lower(),
        }
        await self._hook_plugin_ctx.notify(
            "POST_SIGNUP",
            (action.email, user.uuid, initial_user_prefs),
        )
        return SignupActionResult(
            user_id=user.uuid,
            access_key=ak,
            secret_key=sk,
        )

    async def signout(self, action: SignoutAction) -> SignoutActionResult:
        if action.email != action.requester_email:
            raise GenericForbidden("Not the account owner")
        email = action.email
        result = await check_credential(
            db=self._db,
            domain=action.domain_name,
            email=email,
            password=action.password,
        )
        if result is None:
            raise GenericBadRequest("Invalid email and/or password")
        async with self._db.begin() as conn:
            # Inactivate the user.
            query = users.update().values(status=UserStatus.INACTIVE).where(users.c.email == email)
            await conn.execute(query)
            # Inactivate every keypairs of the user.
            query = keypairs.update().values(is_active=False).where(keypairs.c.user_id == email)
            await conn.execute(query)

        return SignoutActionResult(success=True)

    async def update_full_name(self, action: UpdateFullNameAction) -> UpdateFullNameActionResult:
        email = action.email
        domain_name = action.domain_name
        async with self._db.begin() as conn:
            query = (
                sa.select([users])
                .select_from(users)
                .where(
                    (users.c.email == email) & (users.c.domain_name == domain_name),
                )
            )
            result = await conn.execute(query)
            user = result.first()
            if user is None:
                return UpdateFullNameActionResult(success=False)

            # If user is not null, then it updates user full_name.
            data = {
                "full_name": action.full_name,
            }
            update_query = users.update().values(data).where(users.c.email == email)
            await conn.execute(update_query)
            return UpdateFullNameActionResult(success=True)

    async def update_password(self, action: UpdatePasswordAction) -> UpdatePasswordActionResult:
        domain_name = action.domain_name
        email = action.email
        log_fmt = "AUTH.UPDATE_PASSWORD(d:{}, email:{})"
        log_args = (domain_name, email)
        user = await check_credential(
            db=self._db,
            domain=domain_name,
            email=email,
            password=action.old_password,
        )
        if user is None:
            log.info(log_fmt + ": old password mismtach", *log_args)
            raise AuthorizationFailed("Old password mismatch")
        if action.new_password != action.new_password_confirm:
            log.info(log_fmt + ": new password mismtach", *log_args)
            return UpdatePasswordActionResult(
                success=False,
                message="new password mismatch",
            )

        # [Hooking point for VERIFY_PASSWORD_FORMAT with the ALL_COMPLETED requirement]
        # The hook handlers should accept the request and whole ``params` dict.
        # They should return None if the validation is successful and raise the
        # Reject error otherwise.
        hook_result = await self._hook_plugin_ctx.dispatch(
            "VERIFY_PASSWORD_FORMAT",
            (action.request, action.hook_params),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            hook_result.reason = hook_result.reason or "invalid password format"
            raise RejectedByHook.from_hook_result(hook_result)

        async with self._db.begin() as conn:
            # Update user password.
            data = {
                "password": action.new_password,
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = users.update().values(data).where(users.c.email == email)
            await conn.execute(query)

        return UpdatePasswordActionResult(
            success=True,
            message="Password updated successfully",
        )

    async def update_password_no_auth(
        self, action: UpdatePasswordNoAuthAction
    ) -> UpdatePasswordNoAuthActionResult:
        if action.auth_config is None or action.auth_config.max_password_age is None:
            raise GenericBadRequest("Unsupported function.")

        checked_user = await check_credential(
            db=self._db,
            domain=action.domain_name,
            email=action.email,
            password=action.current_password,
        )
        if checked_user is None:
            raise AuthorizationFailed("User credential mismatch.")
        new_password = action.new_password
        if compare_to_hashed_password(new_password, checked_user["password"]):
            raise AuthorizationFailed("Cannot update to the same password as an existing password.")

        # [Hooking point for VERIFY_PASSWORD_FORMAT with the ALL_COMPLETED requirement]
        # The hook handlers should accept the request and whole ``params` dict.
        # They should return None if the validation is successful and raise the
        # Reject error otherwise.
        hook_result = await self._hook_plugin_ctx.dispatch(
            "VERIFY_PASSWORD_FORMAT",
            (action.request, action.hook_params),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            hook_result.reason = hook_result.reason or "invalid password format"
            raise RejectedByHook.from_hook_result(hook_result)

        async def _update() -> datetime:
            async with self._db.begin() as conn:
                # Update user password.
                data = {
                    "password": new_password,
                    "need_password_change": False,
                    "password_changed_at": sa.func.now(),
                }
                query = (
                    sa.update(users)
                    .values(data)
                    .where(users.c.uuid == checked_user["uuid"])
                    .returning(users.c.password_changed_at)
                )
                result = await conn.execute(query)
                return result.scalar()

        changed_at = await execute_with_retry(_update)

        return UpdatePasswordNoAuthActionResult(
            user_id=checked_user["uuid"],
            password_changed_at=changed_at,
        )

    async def get_ssh_keypair(self, action: GetSSHKeypairAction) -> GetSSHKeypairActionResult:
        async with self._db.begin() as conn:
            # Get SSH public key. Return partial string from the public key just for checking.
            query = sa.select([keypairs.c.ssh_public_key]).where(
                keypairs.c.access_key == action.access_key
            )
            pubkey = await conn.scalar(query)

            return GetSSHKeypairActionResult(public_key=pubkey)

    async def generate_ssh_keypair(
        self, action: GenerateSSHKeypairAction
    ) -> GenerateSSHKeypairActionResult:
        async with self._db.begin() as conn:
            pubkey, privkey = generate_ssh_keypair()
            data = {
                "ssh_public_key": pubkey,
                "ssh_private_key": privkey,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == action.access_key)
            await conn.execute(query)

        return GenerateSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key=pubkey,
                ssh_private_key=privkey,
            )
        )

    async def upload_ssh_keypair(
        self, action: UploadSSHKeypairAction
    ) -> UploadSSHKeypairActionResult:
        privkey = action.private_key
        pubkey = action.public_key
        is_valid, err_msg = validate_ssh_keypair(privkey, pubkey)
        if not is_valid:
            raise InvalidAPIParameters(err_msg)
        async with self._db.begin() as conn:
            data = {
                "ssh_public_key": pubkey,
                "ssh_private_key": privkey,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == action.access_key)
            await conn.execute(query)

        return UploadSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key=pubkey,
                ssh_private_key=privkey,
            ),
        )

    async def _check_password_age(self, user: Row, auth_config: Optional[AuthConfig]) -> None:
        if (
            auth_config is not None
            and (max_password_age := auth_config.max_password_age) is not None
        ):
            password_changed_at: datetime = user.users_password_changed_at

            async with self._db.begin_readonly() as db_conn:
                current_dt: datetime = await db_conn.scalar(sa.select(sa.func.now()))
                if password_changed_at + max_password_age < current_dt:
                    # Force user to update password
                    raise PasswordExpired(
                        extra_msg=f"Password expired on {password_changed_at + max_password_age}."
                    )
