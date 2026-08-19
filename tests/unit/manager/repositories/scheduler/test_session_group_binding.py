"""``sessions.session_group_id`` binding at enqueue time (BEP-1064)."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.session.options import (
    SchedulingTarget,
    SessionHandlerOptions,
    SessionOptions,
)
from ai.backend.manager.data.session.spec import (
    SessionClassification,
    SessionIdentity,
    SessionNetwork,
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.repositories.scheduler.creators import SessionRowFromSpec


def _spec(session_group_id: SessionGroupID | None) -> SessionSpec:
    return SessionSpec(
        resource_spec=SessionResourceSpec(
            identity=SessionIdentity(
                session_id=SessionID(uuid.uuid4()),
                creation_id="c-1",
                session_name="s-1",
                access_key=AccessKey("AK"),
                user_uuid=uuid.uuid4(),
            ),
            classification=SessionClassification(session_type=SessionTypes.INFERENCE),
            network=SessionNetwork(network_type=NetworkType.VOLATILE),
            options=SessionOptions(
                priority=10,
                is_preemptible=False,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                scheduling_target=SchedulingTarget(),
                kernel_groups=[],
                handler_options=SessionHandlerOptions(),
            ),
            kernel_specs=(),
        ),
        scope=SessionScope(
            domain_id=DomainID(uuid.uuid4()),
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            resource_group_name=ResourceGroupName("default"),
            session_group_id=session_group_id,
        ),
    )


class TestSessionGroupBinding:
    @pytest.fixture
    def enqueue_time(self) -> datetime:
        return datetime.now().astimezone()

    def test_grouped_session_carries_the_group(self, enqueue_time: datetime) -> None:
        # A route session inherits its replica group's SessionGroup.
        group_id = SessionGroupID(uuid.uuid4())
        row = SessionRowFromSpec(
            spec=_spec(group_id), image_infos={}, enqueue_time=enqueue_time
        ).build_row()

        assert row.session_group_id == group_id

    def test_ungrouped_session_stays_null(self, enqueue_time: datetime) -> None:
        # Ordinary sessions never join a group — NULL means "no placement
        # constraint" and the RG strategy alone decides placement.
        row = SessionRowFromSpec(
            spec=_spec(None), image_infos={}, enqueue_time=enqueue_time
        ).build_row()

        assert row.session_group_id is None
