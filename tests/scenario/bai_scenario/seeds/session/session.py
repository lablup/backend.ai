"""Write specs for a session."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import AccessKey, ClusterMode, SessionTypes
from ai.backend.manager.data.network.types import NetworkType
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.session.options import (
    SchedulingTarget,
    SessionHandlerOptions,
    SessionOptions,
)
from ai.backend.manager.data.session.spec import (
    KernelSpec,
    SessionClassification,
    SessionIdentity,
    SessionNetwork,
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.session.creators import SessionCreator
from bai_scenario.seeds.seeder import Naming, SeedRowFromThree


def session_spec(
    *,
    session_id: SessionID,
    name: str,
    access_key: AccessKey,
    user_uuid: uuid.UUID,
    domain_id: DomainID,
    domain_name: str,
    project_id: ProjectID,
    resource_group_id: ResourceGroupID,
    resource_group_name: str,
    kernel_specs: tuple[KernelSpec, ...] = (),
) -> SessionSpec:
    """The spec the session row and the kernel rows under it are built from.

    Both the session seed and the kernel seed build it, so a kernel carries the same
    scope its session was enqueued in.
    """
    return SessionSpec(
        resource_spec=SessionResourceSpec(
            identity=SessionIdentity(
                session_id=session_id,
                creation_id=name,
                session_name=name,
                access_key=access_key,
                user_uuid=user_uuid,
            ),
            classification=SessionClassification(session_type=SessionTypes.INTERACTIVE),
            network=SessionNetwork(network_type=NetworkType.VOLATILE),
            options=SessionOptions(
                priority=0,
                is_preemptible=False,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                scheduling_target=SchedulingTarget(),
                kernel_groups=[],
                handler_options=SessionHandlerOptions(),
            ),
            kernel_specs=kernel_specs,
        ),
        scope=SessionScope(
            domain_id=domain_id,
            domain_name=DomainName(domain_name),
            project_id=project_id,
            resource_group_id=resource_group_id,
            resource_group_name=ResourceGroupName(resource_group_name),
        ),
    )


@dataclass(frozen=True)
class SeedSession(SeedRowFromThree[ProjectData, UserData, ResourceGroupData, SessionEntityData]):
    """A session of the given project, owned by the given user, on the given group.

    It waits as enqueued and has no kernel yet; a kernel is laid under it. The access
    key is a value an earlier row answered: the key the session was requested with.
    """

    access_key: AccessKey
    name_hint: str = "session"

    @override
    def kind(self) -> str:
        return "세션"

    @override
    def detail(self) -> str:
        return "스케줄링을 기다리고 있다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self,
        name: str,
        first: ProjectData,
        second: UserData,
        third: ResourceGroupData,
    ) -> SessionCreator:
        return SessionCreator(
            spec=session_spec(
                session_id=SessionID(uuid.uuid4()),
                name=name,
                access_key=self.access_key,
                user_uuid=second.id,
                domain_id=second.domain_id,
                domain_name=first.domain_name,
                project_id=ProjectID(first.id),
                resource_group_id=third.id,
                resource_group_name=third.name,
            ),
            image_infos={},
            enqueue_time=datetime.now(UTC),
        )
