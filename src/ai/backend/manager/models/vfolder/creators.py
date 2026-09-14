"""Insert specs for vfolders."""

from __future__ import annotations

import uuid
from abc import abstractmethod
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_invitation import VFolderInvitationID
from ai.backend.common.data.entity.vfolder_permission import VFolderPermissionID
from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderInvitationState,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermissionData,
)
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.storage import (
    VFolderAlreadyExists,
    VFolderInvalidParameter,
    VFolderNotFound,
    VFolderOwnerNotFound,
)
from ai.backend.manager.models.base import EnumValueType
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.creator import (
    EntityCreator,
    FieldCreator,
    GuardedEntityCreator,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder.row import (
    HARD_DELETED_VFOLDER_STATUSES,
    VFOLDER_NAME_IN_PROJECT_INDEX,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


@dataclass(kw_only=True)
class VFolderBaseCreator(GuardedEntityCreator[VFolderRow, VFolderData]):
    """What every vfolder insert carries, whoever owns it.

    A vfolder is created in a project and nowhere else, so the project column is what
    ``created_in`` reads back off the settled row. The subclasses say which project that
    is, which scope the creation is authorized against, and what the row may not collide
    with.

    The row lands unusable: its storage folder is made after the insert, and the status
    it is made ready with is not one anybody can read or mount.
    """

    name: str
    domain_name: str
    quota_scope_id: str
    host: str
    creator_id: uuid.UUID
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL
    permission: VFolderMountPermission = VFolderMountPermission.READ_WRITE
    cloneable: bool = False
    status: VFolderOperationStatus = VFolderOperationStatus.CREATING

    @abstractmethod
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        """The scope the creation is authorized against.

        The project for a folder that project owns, the person's own scope for a folder
        of their own — not where the folder lands, which the project column answers.
        """
        raise NotImplementedError

    @abstractmethod
    def _allowance(self) -> sa.sql.expression.ColumnElement[int]:
        """How many folders the owner's resource policy allows."""
        raise NotImplementedError

    @abstractmethod
    def _owned_folders_condition(self) -> sa.sql.expression.ColumnElement[bool]:
        """The folders that count toward the owner's allowance."""
        raise NotImplementedError

    @override
    def entity_id(self, row: VFolderRow) -> VFolderUUID:
        return VFolderUUID(row.id)

    @override
    def created_in(self, row: VFolderRow) -> Collection[EntityIdentifier]:
        """The project the row landed in, read back after the insert settled it."""
        if row.group is None:
            raise VFolderOwnerNotFound(f"VFolder '{row.id}' was created in no project.")
        return (ProjectID(row.group),)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        """A name already standing in the project is the database's own answer."""
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=VFolderAlreadyExists(
                    f"VFolder with the given name already exists. ({self.name})"
                ),
                constraint_name=VFOLDER_NAME_IN_PROJECT_INDEX,
            ),
        )

    @override
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        """The owner's folder allowance, spent by what they still hold."""
        return (
            PreconditionCheck(
                finder=self._allowance_spent(),
                error=VFolderInvalidParameter("You cannot create more vfolders."),
            ),
        )

    def _allowance_spent(self) -> sa.Select[Any]:
        """Answers with a row when the owner already holds every folder their policy
        allows.

        The allowance is read in the same statement as the count, so the policy cannot
        change between the two. A policy of zero or less states no limit.
        """
        allowance = self._allowance()
        held = (
            sa.select(sa.func.count())
            .select_from(VFolderRow)
            .where(
                self._owned_folders_condition(),
                VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES),
            )
            .scalar_subquery()
        )
        return sa.select(sa.literal(1)).where(allowance > 0, held >= allowance)

    def _build_row(
        self,
        ownership_type: VFolderOwnershipType,
        user: UserID | None,
        project: ProjectID | sa.ScalarSelect[Any],
        permission: VFolderMountPermission | sa.Case[Any] | None = None,
    ) -> VFolderRow:
        """The row every vfolder insert writes.

        ``project`` and ``permission`` take either a value or the SQL that computes one:
        a personal folder names its project by its owner, and a model store folder takes
        its mount mode from the project rather than from the request.
        """
        return VFolderRow(
            name=self.name,
            domain_name=self.domain_name,
            quota_scope_id=QuotaScopeID.parse(self.quota_scope_id),
            usage_mode=self.usage_mode,
            permission=self.permission if permission is None else permission,
            last_used=None,
            host=self.host,
            creator=self._creator_email(),
            creator_id=self.creator_id,
            ownership_type=ownership_type,
            user=user,
            group=project,
            unmanaged_path=None,
            cloneable=self.cloneable,
            status=self.status,
        )

    def _creator_email(self) -> sa.ScalarSelect[str]:
        """The address of whoever made the folder, which the row keeps beside the id."""
        return sa.select(UserRow.email).where(UserRow.uuid == self.creator_id).scalar_subquery()

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()


@dataclass(kw_only=True)
class PersonalVFolderCreator(VFolderBaseCreator):
    """A folder one person owns, created in that person's personal project.

    The project is not an input: the insert names it by the owner, so no request can
    address somebody else's personal project. Sharing is what puts an entity there.
    """

    user: UserID

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.user,)

    @override
    def build_row(self) -> VFolderRow:
        return self._build_row(
            VFolderOwnershipType.USER,
            self.user,
            sa.select(ProjectRow.id)
            .where(
                ProjectRow.creator_id == self.user,
                ProjectRow.type == ProjectType.PERSONAL,
            )
            .scalar_subquery(),
        )

    @override
    def _owned_folders_condition(self) -> sa.sql.expression.ColumnElement[bool]:
        return VFolderRow.user == self.user

    @override
    def _allowance(self) -> sa.sql.expression.ColumnElement[int]:
        return (
            sa.select(UserResourcePolicyRow.max_vfolder_count)
            .select_from(UserRow)
            .join(
                UserResourcePolicyRow,
                UserResourcePolicyRow.name == UserRow.resource_policy,
            )
            .where(UserRow.uuid == self.user)
            .scalar_subquery()
        )


@dataclass(kw_only=True)
class ProjectVFolderCreator(VFolderBaseCreator):
    """A folder a project owns, created in that project. No user owns it."""

    project: ProjectID

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project,)

    @override
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        """What the allowance says, plus what the named project may not be.

        A personal project is never addressed by a request: a folder under somebody's
        own name is theirs to create, and sharing is what puts one into anyone else's.
        A model store holds model folders only.
        """
        checks = [
            *super().precondition_checks(),
            PreconditionCheck(
                finder=self._project_of_type(ProjectType.PERSONAL),
                error=VFolderInvalidParameter(
                    "A personal project cannot be named as the target of a vfolder. "
                    "Omit the project to create your own folder."
                ),
            ),
        ]
        if self.usage_mode != VFolderUsageMode.MODEL:
            checks.append(
                PreconditionCheck(
                    finder=self._project_of_type(ProjectType.MODEL_STORE),
                    error=VFolderInvalidParameter(
                        "Only Model VFolder can be created under the model store project"
                    ),
                )
            )
        return tuple(checks)

    def _project_of_type(self, project_type: ProjectType) -> sa.Select[Any]:
        return sa.select(ProjectRow.id).where(
            ProjectRow.id == self.project, ProjectRow.type == project_type
        )

    @override
    def build_row(self) -> VFolderRow:
        """A model store folder is read-only to everyone but whoever made it, which the
        insert reads off the project rather than the request."""
        permission_type = EnumValueType(VFolderMountPermission)
        return self._build_row(
            VFolderOwnershipType.GROUP,
            None,
            self.project,
            sa.case(
                (
                    self._project_of_type(ProjectType.MODEL_STORE).exists(),
                    sa.literal(VFolderMountPermission.READ_ONLY, permission_type),
                ),
                else_=sa.literal(self.permission, permission_type),
            ),
        )

    @override
    def _owned_folders_condition(self) -> sa.sql.expression.ColumnElement[bool]:
        return sa.and_(
            VFolderRow.group == self.project,
            VFolderRow.ownership_type == VFolderOwnershipType.GROUP,
        )

    @override
    def _allowance(self) -> sa.sql.expression.ColumnElement[int]:
        return (
            sa.select(ProjectResourcePolicyRow.max_vfolder_count)
            .select_from(ProjectRow)
            .join(
                ProjectResourcePolicyRow,
                ProjectResourcePolicyRow.name == ProjectRow.resource_policy,
            )
            .where(ProjectRow.id == self.project)
            .scalar_subquery()
        )


@dataclass(kw_only=True)
class UnmanagedVFolderMixin(VFolderBaseCreator):
    """A folder pointing at a path the manager does not own.

    Its contents are outside what Backend.AI put there, so the folder is not made and
    not reclaimed — the row only names where it is. Who it belongs to is a separate
    question, so this rides on either owner; whether an account may say it at all is
    settled where the request is read.
    """

    unmanaged_path: str

    def _with_unmanaged_path(self, row: VFolderRow) -> VFolderRow:
        row.unmanaged_path = self.unmanaged_path
        return row


@dataclass(kw_only=True)
class UnmanagedPersonalVFolderCreator(UnmanagedVFolderMixin, PersonalVFolderCreator):
    """One person's folder over a path the manager does not own."""

    @override
    def build_row(self) -> VFolderRow:
        return self._with_unmanaged_path(super().build_row())


@dataclass(kw_only=True)
class UnmanagedProjectVFolderCreator(UnmanagedVFolderMixin, ProjectVFolderCreator):
    """A project's folder over a path the manager does not own."""

    @override
    def build_row(self) -> VFolderRow:
        return self._with_unmanaged_path(super().build_row())


@dataclass
class VFolderPermissionCreator(
    FieldCreator[VFolderUUID, VFolderPermissionRow, VFolderPermissionData]
):
    """Records one user's mount permission on a vfolder.

    The legacy row the mount path reads. Access itself is the grant recorded beside it;
    this says nothing about the RBAC graph.
    """

    user_id: uuid.UUID
    permission: VFolderMountPermission

    @override
    def field_id(self, row: VFolderPermissionRow) -> VFolderPermissionID:
        return VFolderPermissionID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=VFolderNotFound(),
            ),
        )

    @override
    def build_row(self, owner_id: VFolderUUID) -> VFolderPermissionRow:
        return VFolderPermissionRow(
            vfolder=owner_id,
            user=self.user_id,
            permission=self.permission,
        )

    @override
    def to_data(self, row: VFolderPermissionRow) -> VFolderPermissionData:
        return VFolderPermissionData(
            id=VFolderPermissionID(row.id),
            vfolder=row.vfolder,
            user=row.user,
            permission=row.permission or VFolderMountPermission.READ_WRITE,
        )


@dataclass(kw_only=True)
class VFolderInvitationCreator(EntityCreator[VFolderInvitationRow, VFolderInvitationID]):
    """Creator for an invitation to share one vfolder.

    The invitation is created in the vfolder it invites to, which owns and governs it;
    the invitee acts on it while holding no permission on the folder itself.
    """

    vfolder_id: VFolderUUID
    inviter_email: str
    invitee_email: str
    permission: VFolderMountPermission

    @override
    def entity_id(self, row: VFolderInvitationRow) -> EntityIdentifier:
        return VFolderInvitationID(row.id)

    @override
    def created_in(self, row: VFolderInvitationRow) -> Collection[EntityIdentifier]:
        return (VFolderUUID(row.vfolder),)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> VFolderInvitationRow:
        return VFolderInvitationRow(
            permission=self.permission,
            vfolder=self.vfolder_id,
            inviter=self.inviter_email,
            invitee=self.invitee_email,
            state=VFolderInvitationState.PENDING,
        )

    @override
    def to_data(self, row: VFolderInvitationRow) -> VFolderInvitationID:
        return VFolderInvitationID(row.id)
