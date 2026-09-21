"""Fair share search operations the current rules ban.

A filter or an order on another entity's column cannot ask whether the caller may read
that row, so `models/specs/search/AGENTS.md` bans it. What is here shipped before the
rule, is marked deprecated in the schema, and is removed in the next release. Nothing
new goes here; the declarations are in `searchable_fields.py`.

Both reads use these. The read rooted at the fair share table reaches the other entity
through an outer join; the read rooted at the domain, project or membership row keeps
every entity of the resource group and leaves the fair share columns NULL where no row
exists, so there the name, the id and the status are read off the base table.
"""

from __future__ import annotations

from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "DeprecatedDomainFairShareFields",
    "DeprecatedProjectFairShareFields",
    "DeprecatedUserFairShareFields",
)


class DeprecatedDomainFairShareFields:
    """The domain columns a domain fair share read reaches."""

    name = SearchableField(
        DomainRow.name, StringConditions(DomainRow.name), ColumnOrder(DomainRow.name)
    )
    is_active = SearchableField(
        DomainRow.is_active, BoolConditions(DomainRow.is_active), ColumnOrder(DomainRow.is_active)
    )


class DeprecatedProjectFairShareFields:
    """The project columns a project fair share read reaches."""

    id = SearchableField(ProjectRow.id, UUIDConditions(ProjectRow.id), ColumnOrder(ProjectRow.id))
    name = SearchableField(
        ProjectRow.name, StringConditions(ProjectRow.name), ColumnOrder(ProjectRow.name)
    )
    is_active = SearchableField(
        ProjectRow.is_active,
        BoolConditions(ProjectRow.is_active),
        ColumnOrder(ProjectRow.is_active),
    )
    domain_name = SearchableField(
        DomainRow.name, StringConditions(DomainRow.name), ColumnOrder(DomainRow.name)
    )


class DeprecatedUserFairShareFields:
    """The user columns a user fair share read reaches."""

    uuid = SearchableField(UserRow.uuid, UUIDConditions(UserRow.uuid), ColumnOrder(UserRow.uuid))
    username = SearchableField(
        UserRow.username,
        StringConditions(UserRow.username),
        ColumnOrder(UserRow.username),
    )
    email = SearchableField(
        UserRow.email,
        StringConditions(UserRow.email),
        ColumnOrder(UserRow.email),
    )
    status = SearchableField(
        UserRow.status, EnumConditions(UserRow.status, UserStatus), ColumnOrder(UserRow.status)
    )
    domain_name = SearchableField(
        DomainRow.name, StringConditions(DomainRow.name), ColumnOrder(DomainRow.name)
    )
    membership_user_id = SearchableField(
        AssocGroupUserRow.user_id,
        UUIDConditions(AssocGroupUserRow.user_id),
        ColumnOrder(AssocGroupUserRow.user_id),
    )
    membership_project_id = SearchableField(
        AssocGroupUserRow.group_id,
        UUIDConditions(AssocGroupUserRow.group_id),
        ColumnOrder(AssocGroupUserRow.group_id),
    )
