from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.types import SearchScope
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class SearchLoginSessionsAction(AuthAction):
    scope: SearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchLoginSessionsActionResult(SearchActionResult[LoginSessionData]):
    pass
