from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.login_client_type import LoginClientTypeID
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_client_type.searchable_fields import (
    LoginClientTypeSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("LoginClientTypeUpserter",)


@dataclass
class LoginClientTypeUpserter(
    CreatedInPublic[LoginClientTypeRow],
    EntityUpserter[LoginClientTypeRow, LoginClientTypeData],
):
    """Upserter for a login client type under its stated id.

    Conflict key: ``id``. A name another row holds fails on the unique constraint.
    """

    id: LoginClientTypeID
    name: str
    description: str | None

    @override
    def entity_id(self, row: LoginClientTypeRow) -> LoginClientTypeID:
        return LoginClientTypeID(row.id)

    @override
    def row_class(self) -> type[LoginClientTypeRow]:
        return LoginClientTypeRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "description": self.description}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {"name": self.name, "description": self.description, "updated_at": sa.func.now()}

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return LoginClientTypeSearchableFields.own.to_data(row)
