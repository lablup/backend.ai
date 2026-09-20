"""What a project search can filter and order by, and how a project row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.manager.data.project.types import ProjectData, ProjectStatus, ProjectType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.membership import MembershipConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation, ToOneCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists


class _ProjectOwnFields(RowDataConverter[ProjectRow, ProjectData]):
    """The project's own columns."""

    id = SearchableField(ProjectRow.id, UUIDConditions(ProjectRow.id), ColumnOrder(ProjectRow.id))
    name = SearchableField(
        ProjectRow.name,
        StringConditions(sa.type_coerce(ProjectRow.name, sa.String())),
        ColumnOrder(ProjectRow.name),
    )
    description = SearchableField(
        ProjectRow.description,
        StringConditions(ProjectRow.description),
        ColumnOrder(ProjectRow.description),
    )
    is_active = SearchableField(
        ProjectRow.is_active,
        BoolConditions(ProjectRow.is_active),
        ColumnOrder(ProjectRow.is_active),
    )
    status = SearchableField(
        ProjectRow.status,
        EnumConditions(ProjectRow.status, ProjectStatus),
        ColumnOrder(ProjectRow.status),
    )
    created_at = SearchableField(
        ProjectRow.created_at,
        DateTimeConditions(ProjectRow.created_at),
        ColumnOrder(ProjectRow.created_at),
    )
    modified_at = SearchableField(
        ProjectRow.updated_at,
        DateTimeConditions(ProjectRow.updated_at),
        ColumnOrder(ProjectRow.updated_at),
    )
    integration_name = SearchableField(
        ProjectRow.integration_id,
        StringConditions(ProjectRow.integration_id),
        ColumnOrder(ProjectRow.integration_id),
    )
    domain_name = SearchableField(
        ProjectRow.domain_name,
        StringConditions(ProjectRow.domain_name),
        ColumnOrder(ProjectRow.domain_name),
    )
    resource_policy = SearchableField(
        ProjectRow.resource_policy,
        StringConditions(ProjectRow.resource_policy),
        ColumnOrder(ProjectRow.resource_policy),
    )
    type = SearchableField(
        ProjectRow.type,
        EnumConditions(ProjectRow.type, ProjectType),
        ColumnOrder(ProjectRow.type),
    )
    creator_id = SearchableField(
        ProjectRow.creator_id,
        UUIDConditions(ProjectRow.creator_id),
        ColumnOrder(ProjectRow.creator_id),
    )
    total_resource_slots = SearchableField(ProjectRow.total_resource_slots, None, None)
    """Impossible: a JSON document of slot names to amounts."""
    allowed_vfolder_hosts = SearchableField(ProjectRow.allowed_vfolder_hosts, None, None)
    """Impossible: a JSON document of hosts to permission sets."""
    container_registry = SearchableField(ProjectRow.container_registry, None, None)
    """Impossible: a structured JSON document."""
    dotfiles = SearchableField(ProjectRow.dotfiles, None, None)
    """Sensitive: user-written files that can hold credentials verbatim. Binary as well."""

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return ProjectData(
            id=self.id.read(row),
            name=self.name.read(row),
            description=self.description.read(row),
            is_active=self.is_active.read(row),
            created_at=self.created_at.read(row),
            modified_at=self.modified_at.read(row),
            integration_name=self.integration_name.read(row),
            domain_name=self.domain_name.read(row),
            total_resource_slots=self.total_resource_slots.read(row),
            allowed_vfolder_hosts=self.allowed_vfolder_hosts.read(row),
            dotfiles=self.dotfiles.read(row),
            resource_policy=self.resource_policy.read(row),
            type=self.type.read(row),
            container_registry=self.container_registry.read(row),
        )


class _ProjectMembershipConditions(MembershipConditions):
    """Project membership, also asked by the holding domain's name."""

    def held_by_domain_name(self, domain_name: str) -> QueryCondition:
        """The projects the named domain holds."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            domain_id = (
                sa.select(DomainRow.id).where(DomainRow.name == domain_name).scalar_subquery()
            )
            return scope_membership_exists(
                DomainEntityType(), domain_id, self._member_type, self._member_id
            )

        return inner


class _ProjectLinkedEntities:
    """How a project connects to other entities; the other entity's permission governs."""

    membership = _ProjectMembershipConditions(ProjectEntityType(), ProjectRow.id)
    domain = ToOneCorrelation(DomainRow, ProjectRow, DomainRow.name == ProjectRow.domain_name)
    """The domain holding the project. Its conditions come from the domain's own module."""
    members = ToManyCorrelation(
        sa.join(AssocGroupUserRow, UserRow, AssocGroupUserRow.user_id == UserRow.uuid),
        ProjectRow,
        AssocGroupUserRow.group_id == ProjectRow.id,
    )
    """The users enrolled in the project. Their conditions come from the user's own module."""


class ProjectSearchableFields:
    own = _ProjectOwnFields()
    linked = _ProjectLinkedEntities
