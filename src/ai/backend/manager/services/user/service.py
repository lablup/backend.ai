import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.dotfile.types import DotfileEntries
from ai.backend.manager.data.user.types import (
    BulkPurgeError,
    BulkUserPurgeResultData,
    UserInfoContext,
)
from ai.backend.manager.errors.storage import DotfileCreationFailed
from ai.backend.manager.errors.user import KeyPairForbidden, UserPurgeFailure
from ai.backend.manager.models.domain.row import verify_dotfile_name
from ai.backend.manager.models.keypair.updaters import (
    KeypairBootstrapScriptUpdater,
    KeypairDotfilesUpdater,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.bootstrap_script import (
    GetBootstrapScriptAction,
    GetBootstrapScriptActionResult,
    UpdateBootstrapScriptAction,
    UpdateBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.actions.create_keypair_dotfile import (
    CreateKeypairDotfileAction,
    CreateKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    BulkCreateUserActionResult,
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_keypair_dotfile import (
    DeleteKeypairDotfileAction,
    DeleteKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.get_user import (
    GetUserAction,
    GetUserActionResult,
)
from ai.backend.manager.services.user.actions.keypair_ops import (
    AdminCreateKeypairAction,
    AdminCreateKeypairActionResult,
    AdminDeleteSSHKeypairAction,
    AdminDeleteSSHKeypairActionResult,
    AdminGetSSHKeypairAction,
    AdminGetSSHKeypairActionResult,
    AdminRegisterSSHKeypairAction,
    AdminRegisterSSHKeypairActionResult,
    AdminSearchKeypairsAction,
    AdminSearchKeypairsActionResult,
    GetKeypairAction,
    GetKeypairActionResult,
    IssueMyKeypairAction,
    IssueMyKeypairActionResult,
    PurgeKeypairAction,
    PurgeKeypairActionResult,
    SearchMyKeypairsAction,
    SearchMyKeypairsActionResult,
    SwitchDefaultAccessKeyAction,
    SwitchDefaultAccessKeyActionResult,
    UpdateKeypairAction,
    UpdateKeypairActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    BulkPurgeUserAction,
    BulkPurgeUserActionResult,
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.update_keypair_dotfile import (
    UpdateKeypairDotfileAction,
    UpdateKeypairDotfileActionResult,
)
from ai.backend.manager.services.user.actions.update_user import (
    BulkUpdateUserAction,
    BulkUpdateUserActionResult,
    UpdateUserAction,
    UpdateUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Any | None


class UserService:
    _storage_manager: StorageSessionManager
    _valkey_stat_client: ValkeyStatClient
    _agent_registry: AgentRegistry
    _user_repository: UserRepository
    _scheduling_controller: SchedulingController

    def __init__(
        self,
        storage_manager: StorageSessionManager,
        valkey_stat_client: ValkeyStatClient,
        agent_registry: AgentRegistry,
        user_repository: UserRepository,
        scheduling_controller: SchedulingController,
    ) -> None:
        self._storage_manager = storage_manager
        self._valkey_stat_client = valkey_stat_client
        self._user_repository = user_repository
        self._agent_registry = agent_registry
        self._scheduling_controller = scheduling_controller

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        user_data_result = await self._user_repository.create_user_validated(
            action.creator, action.group_ids
        )
        return CreateUserActionResult(
            data=user_data_result,
        )

    async def bulk_create_users(self, action: BulkCreateUserAction) -> BulkCreateUserActionResult:
        result = await self._user_repository.bulk_create_users_validated(action.items)
        return BulkCreateUserActionResult(data=result)

    async def update_user(self, action: UpdateUserAction) -> UpdateUserActionResult:
        user_data = await self._user_repository.update_user_by_uuid_validated(action.updater)
        return UpdateUserActionResult(data=user_data)

    async def bulk_modify_users(self, action: BulkUpdateUserAction) -> BulkUpdateUserActionResult:
        result = await self._user_repository.bulk_update_users_validated(action.items)
        return BulkUpdateUserActionResult(data=result)

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        await self._user_repository.delete_user_by_uuid_validated(user_uuid=action.user_id)
        return DeleteUserActionResult()

    async def get_user(self, action: GetUserAction) -> GetUserActionResult:
        """Retrieve a single user by UUID.

        Args:
            action: GetUserAction containing user UUID.

        Returns:
            GetUserActionResult containing user data.

        Raises:
            UserNotFound: If the user with the given UUID does not exist.
        """
        user_data = await self._user_repository.get_user_by_uuid(action.user_id)
        return GetUserActionResult(user=user_data)

    async def purge_user(self, action: PurgeUserAction) -> PurgeUserActionResult:
        admin_user = await self._user_repository.get_user_by_uuid(action.admin_user_id)
        user_info_ctx = UserInfoContext(uuid=admin_user.uuid, email=admin_user.email)
        bulk_action = BulkPurgeUserAction(
            user_ids=[action.user_id],
            admin_user_id=action.admin_user_id,
            purge_shared_vfolders=action.purge_shared_vfolders,
            delegate_endpoint_ownership=action.delegate_endpoint_ownership,
        )
        await self._purge_single_user(action.user_id, bulk_action, user_info_ctx)
        return PurgeUserActionResult(user_uuid=action.user_id)

    async def _purge_single_user(
        self,
        user_uuid: UUID,
        action: BulkPurgeUserAction,
        user_info_ctx: UserInfoContext,
    ) -> None:
        """Purge a single user by UUID.

        This is the UUID-based internal implementation used by bulk_purge_users().
        The existing purge_user() method is email-based.

        Raises ``UserNotFound`` for a user that is not there; a bulk run records that
        as one item's failure.
        """
        await self._user_repository.get_user_by_uuid(user_uuid)

        # Check for active vfolder mounts
        if await self._user_repository.check_user_vfolder_mounted_to_active_kernels(user_uuid):
            raise UserPurgeFailure(
                "Some of user's virtual folders are mounted to active kernels. "
                "Terminate those kernels first.",
            )

        # Handle shared vfolders migration
        if action.purge_shared_vfolders.optional_value():
            await self._user_repository.migrate_shared_vfolders(
                deleted_user_uuid=user_uuid,
                target_user_uuid=user_info_ctx.uuid,
                target_user_email=user_info_ctx.email,
            )

        # Handle endpoint ownership delegation
        if action.delegate_endpoint_ownership.optional_value():
            await self._user_repository.delegate_endpoint_ownership(
                user_uuid=user_uuid,
                target_user_uuid=user_info_ctx.uuid,
            )
            await self._user_repository.delete_endpoints(
                user_uuid=user_uuid,
                delete_destroyed_only=True,
            )
        else:
            await self._user_repository.delete_endpoints(
                user_uuid=user_uuid,
                delete_destroyed_only=False,
            )

        # Handle active sessions
        if active_sessions := await self._user_repository.retrieve_active_sessions(user_uuid):
            await self._scheduling_controller.mark_sessions_for_termination(
                [session.id for session in active_sessions],
                reason=KernelLifecycleEventReason.USER_PURGED.value,
                forced=True,
            )

        # Delete vfolders
        await self._user_repository.delete_user_vfolders(
            user_uuid=user_uuid,
            storage_manager=self._storage_manager,
        )

        # Finally purge the user completely
        await self._user_repository.purge_user_by_uuid(user_uuid)

    async def bulk_purge_users(
        self,
        action: BulkPurgeUserAction,
    ) -> BulkPurgeUserActionResult:
        admin_user = await self._user_repository.get_user_by_uuid(action.admin_user_id)
        user_info_ctx = UserInfoContext(
            uuid=admin_user.uuid,
            email=admin_user.email,
        )

        purged_user_ids: list[UUID] = []
        failures: list[BulkPurgeError] = []

        for user_uuid in action.user_ids:
            try:
                await self._purge_single_user(user_uuid, action, user_info_ctx)
                purged_user_ids.append(user_uuid)
            except Exception as e:
                log.error("Failed to purge user {}: {}", user_uuid, e)
                failures.append(BulkPurgeError(user_id=user_uuid, exception=e))

        return BulkPurgeUserActionResult(
            data=BulkUserPurgeResultData(
                purged_user_ids=purged_user_ids,
                failures=failures,
            ),
        )

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        stats = await self._user_repository.get_user_time_binned_monthly_stats(
            user_uuid=action.user_id,
            valkey_stat_client=self._valkey_stat_client,
        )
        return UserMonthStatsActionResult(stats=stats)

    async def admin_month_stats(
        self, _action: AdminMonthStatsAction
    ) -> AdminMonthStatsActionResult:
        stats = await self._user_repository.get_admin_time_binned_monthly_stats(
            valkey_stat_client=self._valkey_stat_client,
        )
        return AdminMonthStatsActionResult(stats=stats)

    async def issue_my_keypair(self, action: IssueMyKeypairAction) -> IssueMyKeypairActionResult:
        generated = await self._user_repository.issue_my_keypair(user_id=action.user_id)
        return IssueMyKeypairActionResult(generated_data=generated)

    async def get_keypair(self, action: GetKeypairAction) -> GetKeypairActionResult:
        keypair = await self._user_repository.keypair(action.keypair_id)
        return GetKeypairActionResult(keypair=keypair)

    async def update_keypair(self, action: UpdateKeypairAction) -> UpdateKeypairActionResult:
        """Write the keypair's settings. Nothing written means the row is gone or the
        guard refused; one more read tells the two apart."""
        written = await self._user_repository.update_keypair(action.to_updater())
        if written is not None:
            return UpdateKeypairActionResult(keypair=written)
        await self._user_repository.keypair(action.keypair_id)
        raise KeyPairForbidden(
            "Cannot deactivate the default access key. Switch the default access key first."
        )

    async def purge_keypair(self, action: PurgeKeypairAction) -> PurgeKeypairActionResult:
        """Remove the keypair. Nothing removed is told apart the same way a refused
        edit is."""
        removed = await self._user_repository.purge_keypair(action.keypair_id)
        if removed is not None:
            return PurgeKeypairActionResult(keypair=removed)
        await self._user_repository.keypair(action.keypair_id)
        raise KeyPairForbidden(
            "Cannot delete the default access key. Switch the default access key first."
        )

    async def switch_default_access_key(
        self, action: SwitchDefaultAccessKeyAction
    ) -> SwitchDefaultAccessKeyActionResult:
        await self._user_repository.switch_default_access_key(
            user_id=action.user_id, access_key=action.access_key
        )
        return SwitchDefaultAccessKeyActionResult(success=True)

    async def search_my_keypairs(
        self, action: SearchMyKeypairsAction
    ) -> SearchMyKeypairsActionResult:
        """Search keypairs owned by the current user."""
        result = await self._user_repository.search_my_keypairs(
            scope=action.scope(), querier=action.querier
        )
        return SearchMyKeypairsActionResult(result=result)

    async def admin_create_keypair(
        self, action: AdminCreateKeypairAction
    ) -> AdminCreateKeypairActionResult:
        """Admin creates a keypair for a given user."""
        generated = await self._user_repository.admin_create_keypair(
            user_id=action.user_id, creator=action.creator
        )
        return AdminCreateKeypairActionResult(generated_data=generated)

    async def admin_search_keypairs(
        self, action: AdminSearchKeypairsAction
    ) -> AdminSearchKeypairsActionResult:
        """Admin search all keypairs."""
        result = await self._user_repository.admin_search_keypairs(querier=action.querier)
        return AdminSearchKeypairsActionResult(result=result)

    # ------------------------------------------------------------------ admin SSH keypair operations

    async def admin_register_ssh_keypair(
        self, action: AdminRegisterSSHKeypairAction
    ) -> AdminRegisterSSHKeypairActionResult:
        """Admin registers (overwrites) a user's SSH keypair."""
        await self._user_repository.admin_update_ssh_keypair(
            access_key=action.access_key,
            ssh_public_key=action.ssh_public_key,
            ssh_private_key=action.ssh_private_key,
        )
        return AdminRegisterSSHKeypairActionResult(access_key=action.access_key)

    async def admin_delete_ssh_keypair(
        self, action: AdminDeleteSSHKeypairAction
    ) -> AdminDeleteSSHKeypairActionResult:
        """Admin clears a user's SSH keypair."""
        await self._user_repository.admin_clear_ssh_keypair(access_key=action.access_key)
        return AdminDeleteSSHKeypairActionResult(access_key=action.access_key)

    async def admin_get_ssh_keypair(
        self, action: AdminGetSSHKeypairAction
    ) -> AdminGetSSHKeypairActionResult:
        """Admin retrieves a user's SSH public key (never the private key)."""
        ssh_public_key = await self._user_repository.admin_get_ssh_public_key(
            access_key=action.access_key
        )
        return AdminGetSSHKeypairActionResult(
            access_key=action.access_key,
            ssh_public_key=ssh_public_key,
        )

    async def create_dotfile(
        self, action: CreateKeypairDotfileAction
    ) -> CreateKeypairDotfileActionResult:
        if not verify_dotfile_name(action.entry.path):
            raise InvalidAPIParameters("dotfile path is reserved for internal operations.")
        keypair_id, current = await self._read_dotfiles(action.access_key)
        entries = current.added(action.entry)
        await self._write_dotfiles(keypair_id, entries)
        return CreateKeypairDotfileActionResult(entries=entries.entries)

    async def update_dotfile(
        self, action: UpdateKeypairDotfileAction
    ) -> UpdateKeypairDotfileActionResult:
        keypair_id, current = await self._read_dotfiles(action.access_key)
        entries = current.replaced(action.entry)
        await self._write_dotfiles(keypair_id, entries)
        return UpdateKeypairDotfileActionResult(entries=entries.entries)

    async def delete_dotfile(
        self, action: DeleteKeypairDotfileAction
    ) -> DeleteKeypairDotfileActionResult:
        keypair_id, current = await self._read_dotfiles(action.access_key)
        entries = current.removed(action.path)
        await self._write_dotfiles(keypair_id, entries)
        return DeleteKeypairDotfileActionResult(entries=entries.entries)

    async def get_bootstrap_script(
        self, action: GetBootstrapScriptAction
    ) -> GetBootstrapScriptActionResult:
        keypair = await self._user_repository.admin_get_keypair(action.access_key)
        return GetBootstrapScriptActionResult(script=keypair.bootstrap_script)

    async def update_bootstrap_script(
        self, action: UpdateBootstrapScriptAction
    ) -> UpdateBootstrapScriptActionResult:
        script = action.script.strip()
        if len(script) > MAXIMUM_DOTFILE_SIZE:
            raise DotfileCreationFailed("Maximum bootstrap script length reached")
        keypair = await self._user_repository.admin_get_keypair(action.access_key)
        await self._user_repository.update_keypair_column(
            KeypairBootstrapScriptUpdater(keypair_id=keypair.id, script=script)
        )
        return UpdateBootstrapScriptActionResult()

    async def _read_dotfiles(self, access_key: AccessKey) -> tuple[KeyPairID, DotfileEntries]:
        """The keypair's id alongside its entries, so the write keys on the row it read."""
        keypair = await self._user_repository.admin_get_keypair(access_key)
        return keypair.id, DotfileEntries.unpack(keypair.dotfiles)

    async def _write_dotfiles(self, keypair_id: KeyPairID, entries: DotfileEntries) -> None:
        await self._user_repository.update_keypair_column(
            KeypairDotfilesUpdater(keypair_id=keypair_id, dotfiles=entries.pack())
        )
