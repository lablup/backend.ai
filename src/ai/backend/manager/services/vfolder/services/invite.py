import asyncio

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UnreachableError
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
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderInvitationState,
    VFolderOwnershipType,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    ListSentInvitationsAction,
    ListSentInvitationsActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    RevokeInvitedVFolderAction,
    RevokeInvitedVFolderActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
    UpdateInvitedVFolderMountPermissionAction,
    UpdateInvitedVFolderMountPermissionActionResult,
)
from ai.backend.manager.services.vfolder.types import VFolderInvitationInfo

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
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)

        if vfolder_data.name.startswith("."):
            raise Forbidden("Cannot share private dot-prefixed vfolders.")

        # An address with an account gets a mount level with the offer; one without
        # gets the offer alone and mounts at the folder's default once it has one.
        invitee_users = await self._vfolder_repository.get_users_by_emails(action.invitee_emails)
        account_of = {email: UserID(user_id) for user_id, email in invitee_users}

        if account_of and await self._vfolder_repository.check_user_has_vfolder_permission(
            action.vfolder_uuid, list(account_of.values())
        ):
            raise VFolderGrantAlreadyExists(
                "Invitation to this VFolder already sent out to target user"
            )

        # Create invitations; an offer already open to an address is restated instead
        invited_ids: list[str] = []

        for email in action.invitee_emails:
            result = await self._vfolder_repository.create_vfolder_invitation(
                action.vfolder_uuid,
                UserID(action.user_uuid),
                email,
                action.mount_permission,
                invitee_id=account_of.get(email),
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

        # Prevent accepting vfolder with duplicated name
        count = await self._vfolder_repository.count_vfolder_with_name_for_user(
            user_id, vfolder_data.name
        )
        if count > 0:
            raise VFolderAlreadyExists

        # Settle the invitation and share the folder to the invitee
        await self._vfolder_repository.accept_invitation(action.invitation_id, UserID(user_id))

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
            if requester_email is None:
                raise UserNotFound

            # The inviter withdraws the offer; the invitee turns it down
            if requester_email == invitation_data.inviter:
                await self._vfolder_repository.cancel_invitation(action.invitation_id)
            elif requester_email == invitation_data.invitee:
                await self._vfolder_repository.reject_invitation(
                    action.invitation_id, UserID(action.requester_user_uuid)
                )
            else:
                raise Forbidden("Cannot change other user's invitation")

        except (TimeoutError, asyncio.CancelledError):
            raise
        except Exception as e:
            if not isinstance(e, (VFolderInvitationNotFound, VFolderNotFound, Forbidden)):
                raise InternalServerError(f"unexpected error: {e}") from e
            raise
        return RejectInvitationActionResult(action.invitation_id)

    async def update_invitation(
        self, action: UpdateInvitationAction
    ) -> UpdateInvitationActionResult:
        # Update invitation permission (only by inviter)
        await self._vfolder_repository.update_invitation_permission(
            action.invitation_id, UserID(action.requester_user_uuid), action.mount_permission
        )

        return UpdateInvitationActionResult(action.invitation_id)

    async def list_invitation(self, action: ListInvitationAction) -> ListInvitationActionResult:
        # Get requester email
        requester_email = await self._vfolder_repository.get_user_email_by_id(action.user_uuid)
        if requester_email is None:
            raise UserNotFound()

        # Get pending invitations with vfolder info
        invitation_vfolder_pairs = await self._vfolder_repository.get_pending_invitations_for_user(
            UserID(action.user_uuid), requester_email
        )

        invs_info: list[VFolderInvitationInfo] = []
        for invitation_data, vfolder_data in invitation_vfolder_pairs:
            info = VFolderInvitationInfo(
                id=invitation_data.id,
                vfolder_id=invitation_data.vfolder,
                vfolder_name=vfolder_data.name,
                invitee_user_email=invitation_data.invitee,
                inviter_user_email=invitation_data.inviter,
                inviter_username=invitation_data.inviter_username,
                mount_permission=invitation_data.permission,
                created_at=invitation_data.created_at,
                modified_at=invitation_data.modified_at,
                status=VFolderInvitationState.PENDING,  # All returned invitations are pending
            )
            invs_info.append(info)

        return ListInvitationActionResult(requester_user_uuid=action.user_uuid, info=invs_info)

    async def leave_invited_vfolder(
        self, action: LeaveInvitedVFolderAction
    ) -> LeaveInvitedVFolderActionResult:
        vfolder_data = await self._vfolder_repository.get_by_id(action.vfolder_uuid)

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

        # Give back the share the user holds
        await self._vfolder_repository.leave_shared_vfolder(action.vfolder_uuid, user_uuid)

        return LeaveInvitedVFolderActionResult(vfolder_data.id)

    async def revoke_invited_vfolder(
        self, action: RevokeInvitedVFolderAction
    ) -> RevokeInvitedVFolderActionResult:
        await self._vfolder_repository.revoke_shared_vfolder(
            action.vfolder_uuid, action.shared_user_id
        )
        return RevokeInvitedVFolderActionResult(action.vfolder_uuid, action.shared_user_id)

    async def update_invited_vfolder_mount_permission(
        self, action: UpdateInvitedVFolderMountPermissionAction
    ) -> UpdateInvitedVFolderMountPermissionActionResult:
        requester = current_user()
        if requester is None:
            raise UnreachableError("User context is not available")
        await self._vfolder_repository.update_invited_vfolder_mount_permission(
            action.vfolder_uuid,
            action.user_id,
            action.permission,
            sharer_id=UserID(requester.user_id),
        )
        return UpdateInvitedVFolderMountPermissionActionResult(
            action.vfolder_uuid, action.user_id, action.permission
        )

    async def list_sent_invitations(
        self, action: ListSentInvitationsAction
    ) -> ListSentInvitationsActionResult:
        invitation_pairs = await self._vfolder_repository.get_sent_invitations_for_user(
            UserID(action.user_uuid)
        )
        invs_info: list[VFolderInvitationInfo] = []
        for invitation_data, vfolder_data in invitation_pairs:
            info = VFolderInvitationInfo(
                id=invitation_data.id,
                vfolder_id=invitation_data.vfolder,
                vfolder_name=vfolder_data.name,
                invitee_user_email=invitation_data.invitee,
                inviter_user_email=invitation_data.inviter,
                inviter_username=invitation_data.inviter_username,
                mount_permission=invitation_data.permission,
                created_at=invitation_data.created_at,
                modified_at=invitation_data.modified_at,
                status=VFolderInvitationState.PENDING,
            )
            invs_info.append(info)

        return ListSentInvitationsActionResult(invitations=invs_info)
