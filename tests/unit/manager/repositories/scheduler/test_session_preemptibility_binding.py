"""``sessions.is_preemptible`` binding at enqueue time (BEP-1055)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

import pytest

from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
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


@dataclass(frozen=True)
class _PreemptibilityCase:
    is_preemptible: bool
    job_priority: int


class TestSessionPreemptibilityBinding:
    @pytest.fixture
    def enqueue_time(self) -> datetime:
        return datetime.now().astimezone()

    @pytest.fixture
    def spec(self, case: _PreemptibilityCase) -> SessionSpec:
        return SessionSpec(
            resource_spec=SessionResourceSpec(
                identity=SessionIdentity(
                    session_id=SessionID(uuid.uuid4()),
                    creation_id="c-1",
                    session_name="s-1",
                    access_key=AccessKey("AK"),
                    user_uuid=uuid.uuid4(),
                ),
                classification=SessionClassification(session_type=SessionTypes.INTERACTIVE),
                network=SessionNetwork(network_type=NetworkType.VOLATILE),
                options=SessionOptions(
                    priority=10,
                    job_priority=case.job_priority,
                    is_preemptible=case.is_preemptible,
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
            ),
        )

    @pytest.mark.parametrize(
        "case",
        [
            _PreemptibilityCase(is_preemptible=True, job_priority=0),
            # The opt-out must survive: the column defaults to true, so a
            # creator that drops the field silently re-enrolls the session
            # as a preemption victim.
            _PreemptibilityCase(is_preemptible=False, job_priority=-5),
        ],
        ids=lambda case: f"preemptible={case.is_preemptible}",
    )
    def test_resolved_preemptibility_reaches_the_row(
        self, case: _PreemptibilityCase, spec: SessionSpec, enqueue_time: datetime
    ) -> None:
        row = SessionRowFromSpec(spec=spec, image_infos={}, enqueue_time=enqueue_time).build_row()

        assert row.is_preemptible == case.is_preemptible
        assert row.job_priority == case.job_priority
