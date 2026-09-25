"""Login client type search over the scopes a type is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow

__all__ = ("ScopedSearchLoginClientTypesAction",)


@dataclass(frozen=True)
class ScopedSearchLoginClientTypesAction(
    ScopedSearchOpsAction[LoginClientTypeRow, LoginClientTypeData]
):
    """Page through the login client types the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LoginClientTypeEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_login_client_types"
