import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserStatus
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class UserService:
    _storage_manager: StorageSessionManager
    _valkey_stat_client: ValkeyStatClient
    _agent_registry: AgentRegistry
    _user_repository: UserRepository
    _admin_user_repository: AdminUserRepository

    def __init__(
        self,
        storage_manager: StorageSessionManager,
        valkey_stat_client: ValkeyStatClient,
        agent_registry: AgentRegistry,
        user_repository: UserRepository,
        admin_user_repository: AdminUserRepository,
    ) -> None:
        self._storage_manager = storage_manager
        self._valkey_stat_client = valkey_stat_client
        self._user_repository = user_repository
        self._admin_user_repository = admin_user_repository
        self._agent_registry = agent_registry

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        username = action.input.username if action.input.username else action.input.email
        _status = UserStatus.ACTIVE  # TODO: Need to be set in action explicitly not in service (integrate is_active and status)
        if action.input.status is None and action.input.is_active is not None:
            _status = UserStatus.ACTIVE if action.input.is_active else UserStatus.INACTIVE
        if action.input.status is not None:
            _status = action.input.status
        group_ids = [] if action.input.group_ids is None else action.input.group_ids

        user_data = {
            "username": username,
            "email": action.input.email,
            "password": action.input.password,
            "need_password_change": action.input.need_password_change,
            "full_name": action.input.full_name,
            "description": action.input.description,
            "status": _status,
            "status_info": "admin-requested",  # user mutation is only for admin
            "domain_name": action.input.domain_name,
            "role": action.input.role,
            "allowed_client_ip": action.input.allowed_client_ip,
            "totp_activated": action.input.totp_activated,
            "resource_policy": action.input.resource_policy,
            "sudo_session_enabled": action.input.sudo_session_enabled,
        }
        if action.input.container_uid is not None:
            user_data["container_uid"] = action.input.container_uid
        if action.input.container_main_gid is not None:
            user_data["container_main_gid"] = action.input.container_main_gid
        if action.input.container_gids is not None:
            user_data["container_gids"] = action.input.container_gids

        try:
            user_data_result = await self._user_repository.create_user_validated(
                user_data, group_ids
            )
            return CreateUserActionResult(
                data=user_data_result,
                success=True,
            )
        except Exception:
            return CreateUserActionResult(
                data=None,
                success=False,
            )

    async def modify_user(self, action: ModifyUserAction) -> ModifyUserActionResult:
        email = action.email
        data = action.modifier.fields_to_update()
        if data.get("password") is None:
            data.pop("password", None)

        group_ids = action.group_ids.optional_value()

        if not data and group_ids is None:
            return ModifyUserActionResult(data=None, success=False)
        if data.get("status") is None and data.get("is_active") is not None:
            data["status"] = UserStatus.ACTIVE if data["is_active"] else UserStatus.INACTIVE

        if data.get("password") is not None:
            from datetime import datetime

            data["password_changed_at"] = datetime.now()

        try:
            user_data_result = await self._user_repository.update_user_validated(
                email=email,
                updates=data,
                group_ids=group_ids,
                requester_uuid=None,  # No user context available in ModifyUserAction
            )
            return ModifyUserActionResult(
                success=True,
                data=user_data_result,
            )
        except Exception:
            return ModifyUserActionResult(
                success=False,
                data=None,
            )

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        try:
            await self._user_repository.soft_delete_user_validated(
                email=action.email,
                requester_uuid=None,  # No user context available in DeleteUserAction
            )
            return DeleteUserActionResult(success=True)
        except Exception:
            return DeleteUserActionResult(success=False)

    async def purge_user(self, action: PurgeUserAction) -> PurgeUserActionResult:
        email = action.email
        log.info("Purging all records of the user {0}...", email)

        # Check if user exists
        user_data = await self._admin_user_repository.get_by_email_force(email)
        if not user_data:
            raise RuntimeError(f"User not found (email: {email})")

        user_uuid = user_data.uuid

        # Check for active vfolder mounts
        if await self._admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force(
            user_uuid
        ):
            raise RuntimeError(
                "Some of user's virtual folders are mounted to active kernels. "
                "Terminate those kernels first.",
            )

        # Handle shared vfolders migration
        if action.purge_shared_vfolders.optional_value():
            await self._admin_user_repository.migrate_shared_vfolders_force(
                deleted_user_uuid=user_uuid,
                target_user_uuid=action.user_info_ctx.uuid,
                target_user_email=action.user_info_ctx.email,
            )

        # Handle endpoint ownership delegation
        if action.delegate_endpoint_ownership.optional_value():
            await self._admin_user_repository.delegate_endpoint_ownership_force(
                user_uuid=user_uuid,
                target_user_uuid=action.user_info_ctx.uuid,
                target_main_access_key=action.user_info_ctx.main_access_key,
            )
            await self._admin_user_repository.delete_endpoints_force(
                user_uuid=user_uuid,
                delete_destroyed_only=True,
            )
        else:
            await self._admin_user_repository.delete_endpoints_force(
                user_uuid=user_uuid,
                delete_destroyed_only=False,
            )

        # Handle active sessions
        if active_sessions := await self._admin_user_repository.retrieve_active_sessions_force(
            user_uuid
        ):
            tasks = [
                asyncio.create_task(
                    self._agent_registry.destroy_session(
                        session,
                        forced=True,
                        reason=KernelLifecycleEventReason.USER_PURGED,
                    )
                )
                for session in active_sessions
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for sess, result in zip(active_sessions, results):
                if isinstance(result, Exception):
                    log.warning(f"Session {sess.id} not terminated properly: {result}")

        # Delete vfolders
        await self._admin_user_repository.delete_user_vfolders_force(
            user_uuid=user_uuid,
            storage_manager=self._storage_manager,
        )

        # Finally purge the user completely
        await self._admin_user_repository.purge_user_force(email)

        return PurgeUserActionResult(success=True)

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        from uuid import UUID

        stats = await self._user_repository.get_user_time_binned_monthly_stats(
            user_uuid=UUID(action.user_id),
            valkey_stat_client=self._valkey_stat_client,
        )
        return UserMonthStatsActionResult(stats=stats)

    async def admin_month_stats(self, action: AdminMonthStatsAction) -> AdminMonthStatsActionResult:
        stats = await self._admin_user_repository.get_admin_time_binned_monthly_stats_force(
            valkey_stat_client=self._valkey_stat_client,
        )
        return AdminMonthStatsActionResult(stats=stats)
