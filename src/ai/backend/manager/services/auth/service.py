import logging
from collections import ChainMap
from datetime import datetime
from typing import Mapping, Optional, cast

from aiohttp import web

from ai.backend.common.dto.manager.auth.field import AuthTokenType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.plugin.hook import ALL_COMPLETED, FIRST_COMPLETED, PASSED, HookPluginContext
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    EmailAlreadyExistsError,
    GroupMembershipNotFoundError,
    PasswordExpired,
    UserCreationError,
    UserNotFound,
)
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    GenericForbidden,
    InternalServerError,
    ObjectNotFound,
    RejectedByHook,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import (
    generate_keypair,
    generate_ssh_keypair,
    validate_ssh_keypair,
)
from ai.backend.manager.models.user import (
    INACTIVE_USER_STATUSES,
    UserRole,
    UserStatus,
    compare_to_hashed_password,
)
from ai.backend.manager.repositories.auth.repository import AuthRepository
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
    _hook_plugin_ctx: HookPluginContext
    _auth_repository: AuthRepository
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        hook_plugin_ctx: HookPluginContext,
        auth_repository: AuthRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._hook_plugin_ctx = hook_plugin_ctx
        self._auth_repository = auth_repository
        self._config_provider = config_provider

    async def get_role(self, action: GetRoleAction) -> GetRoleActionResult:
        group_role = None
        if action.group_id is not None:
            try:
                # TODO: per-group role is not yet implemented.
                await self._auth_repository.get_group_membership_validated(
                    action.group_id, action.user_id
                )
                group_role = "user"
            except GroupMembershipNotFoundError:
                raise ObjectNotFound(
                    extra_msg="No such project or you are not the member of it.",
                    object_name="project (user group)",
                )

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
        auth_config = self._config_provider.config.auth
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)
        elif hook_result.result:
            # Passed one of AUTHORIZED hook
            user = hook_result.result
        else:
            # No AUTHORIZE hook is defined (proceed with normal login)
            target_password_info = PasswordInfo(
                password=action.password,
                algorithm=auth_config.password_hash_algorithm,
                rounds=auth_config.password_hash_rounds,
                salt_size=auth_config.password_hash_salt_size,
            )
            user = await self._auth_repository.check_credential_with_migration(
                action.domain_name,
                action.email,
                target_password_info=target_password_info,
            )
        if user is None:
            raise AuthorizationFailed("User credential mismatch.")
        if user["status"] == UserStatus.BEFORE_VERIFICATION:
            raise AuthorizationFailed("This account needs email verification.")
        if user["status"] in INACTIVE_USER_STATUSES:
            raise AuthorizationFailed("User credential mismatch.")
        await self._check_password_age(user, auth_config)
        user_row = await self._auth_repository.get_user_row_by_uuid_validated(user["uuid"])
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

        # Check if email already exists.
        if await self._auth_repository.check_email_exists(action.email):
            raise EmailAlreadyExistsError("Email already exists")

        # Create a user.
        # Create PasswordInfo for the new user's password
        auth_config = self._config_provider.config.auth
        password_info = PasswordInfo(
            password=action.password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )

        data = {
            "domain_name": action.domain_name,
            "username": action.username if action.username is not None else action.email,
            "email": action.email,
            "password": password_info,  # Pass PasswordInfo object
            "need_password_change": False,
            "full_name": action.full_name if action.full_name is not None else "",
            "description": action.description if action.description is not None else "",
            "status": UserStatus.INACTIVE,
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
        }

        # Add user to the default group.
        group_name = user_data_overriden.get("group", "default")

        try:
            user = await self._auth_repository.create_user_with_keypair(
                user_data=data,
                keypair_data=kp_data,
                group_name=group_name,
                domain_name=action.domain_name,
            )
        except UserCreationError:
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
        result = await self._auth_repository.check_credential_without_migration(
            action.domain_name,
            email,
            action.password,
        )
        if result is None:
            raise GenericBadRequest("Invalid email and/or password")
        await self._auth_repository.deactivate_user_and_keypairs_validated(email)

        return SignoutActionResult(success=True)

    async def update_full_name(self, action: UpdateFullNameAction) -> UpdateFullNameActionResult:
        success = await self._auth_repository.update_user_full_name_validated(
            action.email, action.domain_name, action.full_name
        )
        return UpdateFullNameActionResult(success=success)

    async def update_password(self, action: UpdatePasswordAction) -> UpdatePasswordActionResult:
        domain_name = action.domain_name
        email = action.email
        log_fmt = "AUTH.UPDATE_PASSWORD(d:{}, email:{})"
        log_args = (domain_name, email)
        if action.new_password != action.new_password_confirm:
            log.info(log_fmt + ": new password mismtach", *log_args)
            return UpdatePasswordActionResult(
                success=False,
                message="new password mismatch",
            )
        user = await self._auth_repository.check_credential_without_migration(
            domain_name,
            email,
            action.old_password,
        )
        if user is None:
            log.info(log_fmt + ": old password mismtach", *log_args)
            raise AuthorizationFailed("Old password mismatch")

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

        # Create PasswordInfo with config values
        auth_config = self._config_provider.config.auth
        password_info = PasswordInfo(
            password=action.new_password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )
        await self._auth_repository.update_user_password_validated(email, password_info)

        return UpdatePasswordActionResult(
            success=True,
            message="Password updated successfully",
        )

    async def update_password_no_auth(
        self, action: UpdatePasswordNoAuthAction
    ) -> UpdatePasswordNoAuthActionResult:
        auth_config = self._config_provider.config.auth
        if auth_config.max_password_age is None:
            raise GenericBadRequest("Unsupported function.")
        checked_user = await self._auth_repository.check_credential_without_migration(
            action.domain_name,
            action.email,
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

        password_info = PasswordInfo(
            password=new_password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )
        changed_at = await self._auth_repository.update_user_password_by_uuid_validated(
            checked_user["uuid"], password_info
        )

        return UpdatePasswordNoAuthActionResult(
            user_id=checked_user["uuid"],
            password_changed_at=changed_at,
        )

    async def get_ssh_keypair(self, action: GetSSHKeypairAction) -> GetSSHKeypairActionResult:
        pubkey = await self._auth_repository.get_ssh_public_key_validated(action.access_key)
        return GetSSHKeypairActionResult(public_key=pubkey or "")

    async def generate_ssh_keypair(
        self, action: GenerateSSHKeypairAction
    ) -> GenerateSSHKeypairActionResult:
        pubkey, privkey = generate_ssh_keypair()
        await self._auth_repository.update_ssh_keypair_validated(action.access_key, pubkey, privkey)

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

        await self._auth_repository.update_ssh_keypair_validated(action.access_key, pubkey, privkey)

        return UploadSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key=pubkey,
                ssh_private_key=privkey,
            ),
        )

    async def _check_password_age(self, user: dict, auth_config: Optional[AuthConfig]) -> None:
        if (
            auth_config is not None
            and (max_password_age := auth_config.max_password_age) is not None
        ):
            password_changed_at: Optional[datetime] = user["password_changed_at"]
            if password_changed_at is None:
                return  # Skip check if password_changed_at is not set

            current_dt: datetime = await self._auth_repository.get_current_time_validated()
            if password_changed_at + max_password_age < current_dt:
                # Force user to update password
                raise PasswordExpired(
                    extra_msg=f"Password expired on {password_changed_at + max_password_age}."
                )
