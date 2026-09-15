from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import InvalidRequestError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    DestroySessionRequest,
    MatchSessionsRequest,
    RenameSessionRequest,
)
from ai.backend.common.dto.manager.session.response import GetSessionInfoResponse
from ai.backend.manager.data.session.types import SessionStatus

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData
    from tests.component.session.conftest import SessionSeedData


class TestSessionOperationGate:
    """A session operation is decided by the gate on the session id, not by whose
    access key the caller holds."""

    async def test_project_manager_gets_member_session_info(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
        project_session_manager: UserFixtureData,
    ) -> None:
        result = await user_registry.session.get_info(session_in_project.session_id)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == SessionStatus.RUNNING.name
        assert result.root["userId"] == str(session_in_project.user_uuid)

    async def test_project_manager_renames_member_session(
        self,
        user_registry: BackendAIClientRegistry,
        admin_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
        project_session_manager: UserFixtureData,
    ) -> None:
        new_name = f"{session_in_project.session_name}-renamed"
        await user_registry.session.rename(
            session_in_project.session_id,
            RenameSessionRequest(session_name=new_name),
        )
        matched = await admin_registry.session.match_sessions(MatchSessionsRequest(id=new_name))
        assert [str(x["id"]) for x in matched.matches] == [str(session_in_project.session_id)]

    async def test_user_without_grant_is_denied(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.session.get_info(session_in_project.session_id)

    async def test_user_without_grant_cannot_rename(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.session.rename(
                session_in_project.session_id,
                RenameSessionRequest(session_name="denied-name"),
            )

    async def test_user_without_grant_cannot_destroy(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.session.destroy(
                session_in_project.session_id,
                DestroySessionRequest(forced=True),
            )

    async def test_user_without_grant_cannot_get_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.session.get_status_history(session_in_project.session_id)


class TestSessionRenameDuplicateName:
    """The new name is checked against the live sessions of the session's owner."""

    async def test_name_held_only_by_caller_session_is_accepted(
        self,
        user_registry: BackendAIClientRegistry,
        admin_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
        project_session_manager: UserFixtureData,
        user_session_seed: SessionSeedData,
    ) -> None:
        await user_registry.session.rename(
            session_in_project.session_id,
            RenameSessionRequest(session_name=user_session_seed.session_name),
        )
        matched = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=user_session_seed.session_name)
        )
        assert [str(x["id"]) for x in matched.matches] == [str(session_in_project.session_id)]

    async def test_name_held_by_owner_session_is_rejected(
        self,
        user_registry: BackendAIClientRegistry,
        session_in_project: SessionSeedData,
        project_session_manager: UserFixtureData,
    ) -> None:
        with pytest.raises(InvalidRequestError):
            await user_registry.session.rename(
                session_in_project.session_id,
                RenameSessionRequest(session_name=session_in_project.session_name),
            )
