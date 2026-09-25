"""What a login client type search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _LoginClientTypeOwnFields(RowDataConverter[LoginClientTypeRow, LoginClientTypeData]):
    """The login client type's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches, so it carries
    equality and membership only.
    """

    id = SearchableField(
        LoginClientTypeRow.id,
        UUIDConditions(LoginClientTypeRow.id),
        ColumnOrder(LoginClientTypeRow.id),
    )
    name = SearchableField(
        LoginClientTypeRow.name,
        StringConditions(LoginClientTypeRow.name),
        ColumnOrder(LoginClientTypeRow.name),
    )
    description = SearchableField(
        LoginClientTypeRow.description,
        StringEqualityConditions(LoginClientTypeRow.description),
        ColumnOrder(LoginClientTypeRow.description),
    )
    created_at = SearchableField(
        LoginClientTypeRow.created_at,
        DateTimeConditions(LoginClientTypeRow.created_at),
        ColumnOrder(LoginClientTypeRow.created_at),
    )
    updated_at = SearchableField(
        LoginClientTypeRow.updated_at,
        DateTimeConditions(LoginClientTypeRow.updated_at),
        ColumnOrder(LoginClientTypeRow.updated_at),
    )

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return LoginClientTypeData(
            id=self.id.read(row),
            name=self.name.read(row),
            description=self.description.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class LoginClientTypeSearchableFields:
    own = _LoginClientTypeOwnFields()
