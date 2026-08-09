from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_client_type import LOGIN_CLIENT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.login_client_type.searchers import LoginClientTypeSearcher


@dataclass
class SearchLoginClientTypesAction(SearchGlobalOpsAction[LoginClientTypeRow, LoginClientTypeData]):
    """Page through the login client type catalog; every authenticated user may."""

    searcher: LoginClientTypeSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return LOGIN_CLIENT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_login_client_types"

    @override
    def to_searcher(self) -> LoginClientTypeSearcher:
        return self.searcher
