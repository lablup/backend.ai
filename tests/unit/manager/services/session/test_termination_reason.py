"""The termination reason ``SessionService`` gives the sessions it terminates."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.manager.services.session.actions.destroy_session import DestroySessionAction
from ai.backend.manager.services.session.actions.terminate_sessions import (
    TerminateSessionsAction,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.views.sokovan.session import MarkTerminatingResult


def _user(role: UserRole) -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=role is not UserRole.USER,
        is_superadmin=role is UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


def _mark_result(session_ids: list[SessionId]) -> MarkTerminatingResult:
    return MarkTerminatingResult(
        cancelled_sessions=[],
        terminating_sessions=list(session_ids),
        force_terminated_sessions=[],
        skipped_sessions=[],
        transitions=[],
    )


@pytest.fixture
def owner() -> UserData:
    return _user(UserRole.USER)


@pytest.fixture
def admin() -> UserData:
    return _user(UserRole.SUPERADMIN)


@pytest.fixture
def owned_session_id() -> SessionId:
    return SessionId(uuid.uuid4())


@pytest.fixture
def others_session_id() -> SessionId:
    return SessionId(uuid.uuid4())


@pytest.fixture
def scheduling_controller() -> MagicMock:
    controller = MagicMock()
    controller.mark_sessions_for_termination = AsyncMock(
        side_effect=lambda session_ids, **_: _mark_result(session_ids)
    )
    return controller


@pytest.fixture
async def session_service(
    scheduling_controller: MagicMock,
    owner: UserData,
    owned_session_id: SessionId,
    others_session_id: SessionId,
) -> SessionService:
    session_repository = MagicMock()
    session_repository.batch_get_owner_id_by_session = AsyncMock(
        return_value={owned_session_id: owner.user_id, others_session_id: uuid.uuid4()}
    )
    session_repository.get_target_session_ids = AsyncMock(return_value=[others_session_id])
    return SessionService(
        SessionServiceArgs(
            agent_registry=MagicMock(),
            event_fetcher=MagicMock(),
            background_task_manager=MagicMock(),
            event_hub=MagicMock(),
            error_monitor=MagicMock(),
            idle_checker_host=MagicMock(),
            session_repository=session_repository,
            scheduler_repository=MagicMock(),
            scheduling_controller=scheduling_controller,
            appproxy_client_pool=MagicMock(),
            user_repository=MagicMock(),
        )
    )


def _reasons(controller: MagicMock) -> dict[SessionId, KernelLifecycleEventReason]:
    return {
        session_id: call.kwargs["reason"]
        for call in controller.mark_sessions_for_termination.await_args_list
        for session_id in call.args[0]
    }


class TestTerminateSessionsReason:
    @pytest.mark.parametrize(
        ("forced", "owner_reason", "others_reason"),
        [
            (
                False,
                KernelLifecycleEventReason.USER_REQUESTED,
                KernelLifecycleEventReason.ADMIN_TERMINATED,
            ),
            (
                True,
                KernelLifecycleEventReason.FORCE_TERMINATED,
                KernelLifecycleEventReason.ADMIN_FORCE_TERMINATED,
            ),
        ],
        ids=["normal", "forced"],
    )
    async def test_a_session_of_another_user_gets_the_admin_reason(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        owner: UserData,
        owned_session_id: SessionId,
        others_session_id: SessionId,
        forced: bool,
        owner_reason: KernelLifecycleEventReason,
        others_reason: KernelLifecycleEventReason,
    ) -> None:
        with with_user_context(owner, triggered_user=owner):
            await session_service.terminate_sessions(
                TerminateSessionsAction(
                    session_ids=[owned_session_id, others_session_id], forced=forced
                )
            )

        assert _reasons(scheduling_controller) == {
            owned_session_id: owner_reason,
            others_session_id: others_reason,
        }

    async def test_the_caller_decides_while_impersonating(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        owner: UserData,
        admin: UserData,
        owned_session_id: SessionId,
    ) -> None:
        with with_user_context(owner, triggered_user=admin):
            await session_service.terminate_sessions(
                TerminateSessionsAction(session_ids=[owned_session_id], forced=False)
            )

        assert _reasons(scheduling_controller) == {
            owned_session_id: KernelLifecycleEventReason.ADMIN_TERMINATED
        }

    async def test_without_a_caller_the_owner_reason_is_kept(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        others_session_id: SessionId,
    ) -> None:
        await session_service.terminate_sessions(
            TerminateSessionsAction(session_ids=[others_session_id], forced=False)
        )

        assert _reasons(scheduling_controller) == {
            others_session_id: KernelLifecycleEventReason.USER_REQUESTED
        }


class TestDestroySessionReason:
    async def test_an_admin_destroying_a_session_of_another_user_gets_the_admin_reason(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        admin: UserData,
        others_session_id: SessionId,
    ) -> None:
        with with_user_context(admin, triggered_user=admin):
            await session_service.destroy_session(
                DestroySessionAction(
                    session_id=SessionID(others_session_id),
                    user_role=UserRole.SUPERADMIN,
                    session_name="others",
                    forced=True,
                    recursive=False,
                    owner_access_key=AccessKey("AKTEST"),
                )
            )

        assert _reasons(scheduling_controller) == {
            others_session_id: KernelLifecycleEventReason.ADMIN_FORCE_TERMINATED
        }
