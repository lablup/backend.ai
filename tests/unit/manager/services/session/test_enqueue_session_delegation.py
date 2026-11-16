"""``SessionService.enqueue_session`` with ``owner_id`` naming another user."""

from __future__ import annotations

import uuid
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

_REQUESTER_ID = UserID(uuid.uuid4())
_OWNER_ID = UserID(uuid.uuid4())
_OWNER_ACCESS_KEY = AccessKey("AKOWNER")
_PROJECT_ID = ProjectID(uuid.uuid4())


def _user(user_id: UserID, role: UserRole, domain_name: str) -> UserData:
    return UserData(
        id=user_id,
        uuid=user_id,
        username="owner",
        email="owner@example.com",
        need_password_change=False,
        full_name=None,
        description=None,
        is_active=True,
        status="active",
        status_info=None,
        created_at=None,
        modified_at=None,
        domain_name=domain_name,
        domain_id=DomainID(uuid.uuid4()),
        role=role,
        resource_policy="default",
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=False,
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
    )


@pytest.fixture
def user_repository() -> MagicMock:
    repository = MagicMock()
    repository.get_user_by_uuid = AsyncMock(return_value=_user(_OWNER_ID, UserRole.USER, "default"))
    repository.default_access_key = AsyncMock(return_value=_OWNER_ACCESS_KEY)
    return repository


@pytest.fixture
def scheduling_controller() -> MagicMock:
    controller = MagicMock()
    controller.enqueue_session_from_draft = AsyncMock(return_value=SessionID(uuid.uuid4()))
    return controller


@pytest.fixture
async def session_service(
    user_repository: MagicMock,
    scheduling_controller: MagicMock,
) -> SessionService:
    session_repository = MagicMock()
    session_repository.resolve_image_by_id = AsyncMock()
    session_repository.get_session_data_by_id = AsyncMock(return_value=MagicMock())
    scheduler_repository = MagicMock()
    scheduler_repository.get_domain_id_by_name = AsyncMock(return_value=DomainID(uuid.uuid4()))
    scheduler_repository.get_resource_group_name_by_id = AsyncMock(
        return_value=ResourceGroupName("default")
    )
    return SessionService(
        SessionServiceArgs(
            agent_registry=MagicMock(),
            event_fetcher=MagicMock(),
            background_task_manager=MagicMock(),
            event_hub=MagicMock(),
            error_monitor=MagicMock(),
            idle_checker_host=MagicMock(),
            session_repository=session_repository,
            scheduler_repository=scheduler_repository,
            scheduling_controller=scheduling_controller,
            appproxy_client_pool=MagicMock(),
            user_repository=user_repository,
        )
    )


@pytest.fixture
def action() -> EnqueueSessionAction:
    return EnqueueSessionAction(
        project_id=_PROJECT_ID,
        session_name="delegated",
        session_type=SessionTypes.INTERACTIVE,
        image_id=uuid.uuid4(),
        resource=SessionResourceSpec(
            entries=[ResourceSlotEntry(resource_type="cpu", quantity="1")],
            resource_group_id=ResourceGroupID(uuid.uuid4()),
        ),
        scheduling=SessionSchedulingSpec(),
        user_id=_REQUESTER_ID,
        user_role=UserRole.USER,
        access_key=AccessKey("AKREQUESTER"),
        domain_name="default",
        group_id=_PROJECT_ID,
        owner_id=_OWNER_ID,
    )


class TestEnqueueSessionDelegation:
    async def test_a_superadmin_enqueues_as_the_owner(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        await session_service.enqueue_session(
            replace(action, user_role=UserRole.SUPERADMIN, domain_name="other")
        )

        draft = scheduling_controller.enqueue_session_from_draft.call_args.args[0]
        assert draft.resource_spec.identity.user_uuid == _OWNER_ID
        assert draft.resource_spec.identity.access_key == _OWNER_ACCESS_KEY

    async def test_a_domain_admin_enqueues_for_a_user_of_the_same_domain(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        await session_service.enqueue_session(replace(action, user_role=UserRole.ADMIN))

        draft = scheduling_controller.enqueue_session_from_draft.call_args.args[0]
        assert draft.resource_spec.identity.user_uuid == _OWNER_ID

    async def test_a_domain_admin_is_refused_a_user_of_another_domain(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        with pytest.raises(InsufficientPrivilege):
            await session_service.enqueue_session(
                replace(action, user_role=UserRole.ADMIN, domain_name="other")
            )

        scheduling_controller.enqueue_session_from_draft.assert_not_called()

    async def test_a_domain_admin_is_refused_a_superadmin_owner(
        self,
        session_service: SessionService,
        user_repository: MagicMock,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        user_repository.get_user_by_uuid.return_value = _user(
            _OWNER_ID, UserRole.SUPERADMIN, "default"
        )

        with pytest.raises(InsufficientPrivilege):
            await session_service.enqueue_session(replace(action, user_role=UserRole.ADMIN))

        scheduling_controller.enqueue_session_from_draft.assert_not_called()

    async def test_a_user_is_refused_another_owner(
        self,
        session_service: SessionService,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        with pytest.raises(InsufficientPrivilege):
            await session_service.enqueue_session(action)

        scheduling_controller.enqueue_session_from_draft.assert_not_called()

    async def test_a_user_naming_themselves_is_not_checked(
        self,
        session_service: SessionService,
        user_repository: MagicMock,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        user_repository.get_user_by_uuid.return_value = _user(
            _REQUESTER_ID, UserRole.USER, "default"
        )

        await session_service.enqueue_session(replace(action, owner_id=_REQUESTER_ID))

        draft = scheduling_controller.enqueue_session_from_draft.call_args.args[0]
        assert draft.resource_spec.identity.user_uuid == _REQUESTER_ID
