"""``SessionService.enqueue_session`` with a session group named."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    ResourceSlotEntry,
    SessionResourceSpec,
    SessionSchedulingSpec,
)
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs

_USER_ID = UserID(uuid.uuid4())
_PROJECT_ID = ProjectID(uuid.uuid4())
_SESSION_GROUP_ID = SessionGroupID(uuid.uuid4())


def _session_group(
    *,
    owner_user_id: UserID = _USER_ID,
    project_id: ProjectID = _PROJECT_ID,
    deleted_at: datetime | None = None,
) -> SessionGroupData:
    return SessionGroupData(
        id=_SESSION_GROUP_ID,
        domain_id=DomainID(uuid.uuid4()),
        project_id=project_id,
        owner_user_id=owner_user_id,
        placement_direction=SessionGroupPlacementDirection.SPREAD,
        placement_enforcement=SessionGroupPlacementEnforcement.PREFERRED,
        created_at=datetime.now(UTC),
        deleted_at=deleted_at,
    )


@pytest.fixture
def scheduler_repository() -> MagicMock:
    repository = MagicMock()
    repository.get_domain_id_by_name = AsyncMock(return_value=DomainID(uuid.uuid4()))
    repository.get_resource_group_name_by_id = AsyncMock(return_value=ResourceGroupName("default"))
    return repository


@pytest.fixture
def scheduling_controller() -> MagicMock:
    controller = MagicMock()
    controller.enqueue_session_from_draft = AsyncMock(return_value=SessionID(uuid.uuid4()))
    return controller


@pytest.fixture
async def session_service(
    scheduler_repository: MagicMock,
    scheduling_controller: MagicMock,
) -> SessionService:
    session_repository = MagicMock()
    session_repository.resolve_image_by_id = AsyncMock()
    session_repository.get_session_data_by_id = AsyncMock(return_value=MagicMock())
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
            user_repository=MagicMock(),
        )
    )


@pytest.fixture
def action() -> EnqueueSessionAction:
    return EnqueueSessionAction(
        project_id=_PROJECT_ID,
        session_name="grouped",
        session_type=SessionTypes.INTERACTIVE,
        image_id=uuid.uuid4(),
        resource=SessionResourceSpec(
            entries=[ResourceSlotEntry(resource_type="cpu", quantity="1")],
            resource_group_id=ResourceGroupID(uuid.uuid4()),
        ),
        scheduling=SessionSchedulingSpec(),
        session_group_id=_SESSION_GROUP_ID,
        user_id=_USER_ID,
        access_key=AccessKey("AKTEST"),
        domain_name="default",
        group_id=_PROJECT_ID,
    )


class TestEnqueueSessionGroup:
    async def test_places_the_session_in_the_owners_group(
        self,
        session_service: SessionService,
        scheduler_repository: MagicMock,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        scheduler_repository.get_session_group = AsyncMock(return_value=_session_group())

        await session_service.enqueue_session(action)

        draft = scheduling_controller.enqueue_session_from_draft.call_args.args[0]
        assert draft.scope.session_group_id == _SESSION_GROUP_ID

    @pytest.mark.parametrize(
        "session_group",
        [
            _session_group(owner_user_id=UserID(uuid.uuid4())),
            _session_group(project_id=ProjectID(uuid.uuid4())),
            _session_group(deleted_at=datetime.now(UTC)),
        ],
        ids=["another-owner", "another-project", "deleted"],
    )
    async def test_refuses_a_group_the_session_cannot_join(
        self,
        session_service: SessionService,
        scheduler_repository: MagicMock,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
        session_group: SessionGroupData,
    ) -> None:
        scheduler_repository.get_session_group = AsyncMock(return_value=session_group)

        with pytest.raises(EntityNotFoundError):
            await session_service.enqueue_session(action)

        scheduling_controller.enqueue_session_from_draft.assert_not_called()

    async def test_enqueues_without_a_group(
        self,
        session_service: SessionService,
        scheduler_repository: MagicMock,
        scheduling_controller: MagicMock,
        action: EnqueueSessionAction,
    ) -> None:
        scheduler_repository.get_session_group = AsyncMock()
        ungrouped = replace(action, session_group_id=None)

        await session_service.enqueue_session(ungrouped)

        scheduler_repository.get_session_group.assert_not_called()
        draft = scheduling_controller.enqueue_session_from_draft.call_args.args[0]
        assert draft.scope.session_group_id is None
