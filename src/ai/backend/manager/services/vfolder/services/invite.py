import asyncio

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import Forbidden, InternalServerError
from ai.backend.manager.errors.storage import (
    VFolderAlreadyExists,
    VFolderGrantAlreadyExists,
    VFolderInvalidParameter,
    VFolderInvitationNotFound,
    VFolderNotFound,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderInvitationState,
    VFolderOwnershipType,
)
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository

from ..actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    RevokeInvitedVFolderAction,
    RevokeInvitedVFolderActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
    UpdateInvitedVFolderMountPermissionAction,
    UpdateInvitedVFolderMountPermissionActionResult,
)
from ..types import VFolderInvitationInfo

# TODO: Detach privilege check from the service.
#       The service should only handle the business logic.
#       The privilege check should be done before calling the service.
#       Invite services should receive invitiation ids which are already checked.


class VFolderInviteService:
    _config_provider: ManagerConfigProvider
    _vfolder_repository: VfolderRepository
    _user_repository: UserRepository

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        vfolder_repository: VfolderRepository,
        user_repository: UserRepository,
    ) -> None:
        self._config_provider = config_provider
        self._vfolder_repository = vfolder_repository
        self._user_repository = user_repository

    async def invite(self, action: InviteVFolderAction) -> InviteVFolderActionResult:
        # Get VFolder data
        user = await self._user_repository.get_user_by_uuid(action.user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, action.user_uuid, user.domain_name
        )
        if not vfolder_data:
            raise VFolderNotFound()

        if vfolder_data.name.startswith("."):
            raise Forbidden("Cannot share private dot-prefixed vfolders.")

        # Get inviter email
        inviter_email = await self._vfolder_repository.get_user_email_by_id(action.user_uuid)
        if not inviter_email:
            raise VFolderNotFound()

        # Get invitee user info by UUIDs
        invitee_users = await self._vfolder_repository.get_users_by_ids(action.invitee_user_uuids)

        # Check if users already have permission
        has_permission = await self._vfolder_repository.check_user_has_vfolder_permission(
            action.vfolder_uuid, action.invitee_user_uuids
        )
        if has_permission:
            raise VFolderGrantAlreadyExists(
                "Invitation to this VFolder already sent out to target user"
            )

        # Create invitations
        invited_ids = []

        for _, user_email in invitee_users:
            # Check if invitation already exists
            invitation_exists = await self._vfolder_repository.check_pending_invitation_exists(
                action.vfolder_uuid, inviter_email, user_email
            )
            if invitation_exists:
                continue

            # Create invitation
            result = await self._vfolder_repository.create_vfolder_invitation(
                action.vfolder_uuid,
                inviter_email,
                user_email,
                action.mount_permission,
            )
            if result:
                invited_ids.append(result)

        return InviteVFolderActionResult(
            vfolder_uuid=action.vfolder_uuid, invitation_ids=invited_ids
        )

    async def accept_invitation(
        self, action: AcceptInvitationAction
    ) -> AcceptInvitationActionResult:
        # Get invitation
        invitation_data = await self._vfolder_repository.get_invitation_by_id(action.invitation_id)
        if not invitation_data:
            raise VFolderInvitationNotFound

        # Get target user by email
        user_info = await self._vfolder_repository.get_user_by_email(invitation_data.invitee)
        if not user_info:
            raise VFolderNotFound
        user_id, _ = user_info

        # Get target vfolder
        vfolder_data = await self._vfolder_repository.get_by_id(invitation_data.vfolder)
        if not vfolder_data:
            raise VFolderNotFound

        # Prevent accepting vfolder with duplicated name
        count = await self._vfolder_repository.count_vfolder_with_name_for_user(
            user_id, vfolder_data.name
        )
        if count > 0:
            raise VFolderAlreadyExists

        # Create permission relation between the vfolder and the invitee
        await self._vfolder_repository.create_vfolder_permission(
            invitation_data.vfolder,
            user_id,
            VFolderMountPermission(invitation_data.permission),
        )

        # Mark invitation as accepted
        await self._vfolder_repository.update_invitation_state(
            action.invitation_id, VFolderInvitationState.ACCEPTED
        )

        return AcceptInvitationActionResult(action.invitation_id)

    async def reject_invitation(
        self,
        action: RejectInvitationAction,
    ) -> RejectInvitationActionResult:
        try:
            # Get invitation
            invitation_data = await self._vfolder_repository.get_invitation_by_id(
                action.invitation_id
            )
            if not invitation_data:
                raise VFolderInvitationNotFound

            # Get requester user email
            requester_email = await self._vfolder_repository.get_user_email_by_id(
                action.requester_user_uuid
            )
            if not requester_email:
                raise VFolderNotFound

            # Determine new state based on who is rejecting
            if requester_email == invitation_data.inviter:
                state = VFolderInvitationState.CANCELED
            elif requester_email == invitation_data.invitee:
                state = VFolderInvitationState.REJECTED
            else:
                raise Forbidden("Cannot change other user's invitation")

            # Update invitation state
            await self._vfolder_repository.update_invitation_state(action.invitation_id, state)

        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            if not isinstance(e, (VFolderInvitationNotFound, VFolderNotFound, Forbidden)):
                raise InternalServerError(f"unexpected error: {e}")
            raise
        return RejectInvitationActionResult(action.invitation_id)

    async def update_invitation(
        self, action: UpdateInvitationAction
    ) -> UpdateInvitationActionResult:
        # Get requester email
        requester_email = await self._vfolder_repository.get_user_email_by_id(
            action.requester_user_uuid
        )
        if not requester_email:
            raise VFolderNotFound()

        # Update invitation permission (only by inviter)
        await self._vfolder_repository.update_invitation_permission(
            action.invitation_id, requester_email, action.mount_permission
        )

        return UpdateInvitationActionResult(action.invitation_id)

    async def list_invitation(self, action: ListInvitationAction) -> ListInvitationActionResult:
        # Get requester email
        requester_email = await self._vfolder_repository.get_user_email_by_id(
            action.requester_user_uuid
        )
        if not requester_email:
            raise VFolderNotFound()

        # Get pending invitations with vfolder info
        invitation_vfolder_pairs = await self._vfolder_repository.get_pending_invitations_for_user(
            requester_email
        )

        invs_info: list[VFolderInvitationInfo] = []
        for invitation_data, vfolder_data in invitation_vfolder_pairs:
            info = VFolderInvitationInfo(
                id=invitation_data.id,
                vfolder_id=invitation_data.vfolder,
                vfolder_name=vfolder_data.name,
                invitee_user_email=invitation_data.invitee,
                inviter_user_email=invitation_data.inviter,
                mount_permission=invitation_data.permission,
                created_at=invitation_data.created_at,
                modified_at=invitation_data.modified_at,
                status=VFolderInvitationState.PENDING,  # All returned invitations are pending
            )
            invs_info.append(info)

        return ListInvitationActionResult(
            requester_user_uuid=action.requester_user_uuid, info=invs_info
        )

    async def leave_invited_vfolder(
        self, action: LeaveInvitedVFolderAction
    ) -> LeaveInvitedVFolderActionResult:
        # Get vfolder info
        user = await self._user_repository.get_user_by_uuid(action.requester_user_uuid)
        vfolder_data = await self._vfolder_repository.get_by_id_validated(
            action.vfolder_uuid, user.id, user.domain_name
        )
        if not vfolder_data:
            raise VFolderNotFound()

        if vfolder_data.ownership_type == VFolderOwnershipType.GROUP:
            raise VFolderInvalidParameter("Cannot leave a group vfolder.")

        # Get requester info
        requester_info = await self._vfolder_repository.get_user_info(action.requester_user_uuid)
        if not requester_info:
            raise VFolderNotFound()
        requester_role, _ = requester_info

        if action.shared_user_uuid:
            # Allow only superadmin to leave the shared vfolder of others.
            if (action.requester_user_uuid != action.shared_user_uuid) and (
                requester_role != UserRole.SUPERADMIN
            ):
                raise InsufficientPrivilege("Insufficient permission.")
            user_uuid = action.shared_user_uuid
        else:
            user_uuid = action.requester_user_uuid

        # Delete vfolder permission
        await self._vfolder_repository.delete_vfolder_permission(action.vfolder_uuid, user_uuid)

        return LeaveInvitedVFolderActionResult(vfolder_data.id)

    async def revoke_invited_vfolder(
        self, action: RevokeInvitedVFolderAction
    ) -> RevokeInvitedVFolderActionResult:
        await self._vfolder_repository.delete_vfolder_permission(
            action.vfolder_id, action.shared_user_id
        )
        return RevokeInvitedVFolderActionResult(action.vfolder_id, action.shared_user_id)

    async def update_invited_vfolder_mount_permission(
        self, action: UpdateInvitedVFolderMountPermissionAction
    ) -> UpdateInvitedVFolderMountPermissionActionResult:
        await self._vfolder_repository.update_invited_vfolder_mount_permission(
            action.vfolder_id, action.user_id, action.permission
        )
        return UpdateInvitedVFolderMountPermissionActionResult(
            action.vfolder_id, action.user_id, action.permission
        )
