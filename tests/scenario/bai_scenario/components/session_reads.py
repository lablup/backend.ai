"""What a session read scenario lays: one session, its kernel and kernel group.

The rows are built the way the manager builds them — a session through its creator, the
kernel group and the kernel under it — and read back through a caller granted the
permission the row's scope allows.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.kernel_group.types import (
    KernelGroupData,
    KernelGroupEnvironData,
    KernelGroupResourceSlotData,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given, Says
from bai_scenario.components.domain import SomeoneOf
from bai_scenario.components.resource_allocation import (
    Granted,
    LaidPlace,
    lay_a_caller_of,
    lay_a_place,
)
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.session.kernel import TestSeedKernelOf, TestSeedMainKernelGroupOf
from bai_scenario.seeds.session.kernel_group_fields import (
    TestSeedKernelGroupEnvironOf,
    TestSeedKernelGroupResourceSlotOf,
)
from bai_scenario.seeds.session.session import TestSeedSession

ENVIRON_KEY = "SCENARIO_SEEDED"
ENVIRON_VALUE = "yes"


@dataclass(frozen=True)
class LaidSessionAndCaller:
    """A session with one kernel group and one kernel, and the user who reads it."""

    domain: DomainData
    project: ProjectData
    resource_group: ResourceGroupData
    owner: UserData
    image: ImageData
    session: SessionEntityData
    group: KernelGroupData
    environ: KernelGroupEnvironData
    group_slot: KernelGroupResourceSlotData
    kernel: KernelInfo
    caller: UserData
    slot_name: str
    quantity: Decimal


@dataclass(frozen=True)
class SomeoneGrantedSessionIn(TestSeedNest[Laid[UserData]]):
    """그 프로젝트 범위에서 세션 권한 하나를 받은 사용자."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    permission: Permission
    role_hint: str

    @override
    def kind(self) -> str:
        return Says(
            "프로젝트 범위의 세션 권한을 받은 사용자 준비",
            english="Prepare a user granted a session permission in the project scope",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint=self.role_hint), self.project
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=self.permission), role
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class ASessionWithAKernelAndSomeone(Given[Any, LaidSessionAndCaller]):
    """One pending session with a kernel and its group, and a caller.

    ``granted`` decides where the caller's session read role sits; ``role`` names the
    caller when no role is granted. ``permission`` is the session permission the grant
    carries when it sits in the project. ``beside_another_outside`` lays the same shape
    beside it in the same project and again in another project, so a scoped read can tell
    them apart from what it returns.
    """

    granted: Granted = Granted.THE_PROJECT
    role: UserRole = UserRole.USER
    permission: Permission = Permission.READ
    beside_another_outside: bool = False

    @override
    def describe(self) -> str:
        if self.beside_another_outside:
            return Says(
                "커널 하나와 그 커널 그룹을 가진 대기 세션, 같은 프로젝트의 같은 모양 세션 "
                "하나와 다른 프로젝트의 같은 모양 세션 하나, 그리고 그것을 읽을 사용자 한 명",
                english=(
                    "one pending session with a kernel and its kernel group, the same shape "
                    "laid beside it in the same project and again in another project, and one "
                    "user who reads it"
                ),
            )
        return Says(
            "커널 하나와 그 커널 그룹을 가진 대기 세션, 그리고 그것을 읽을 사용자 한 명",
            english=(
                "one pending session with a kernel and its kernel group, and one user who reads it"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> LaidSessionAndCaller:
        place = await lay_a_place(seeding, slots=1)
        image = seeding.made(place.image)
        slot_name = seeding.made(place.slot_types[0]).slot_name
        quantity = Decimal(1)
        slots = ((slot_name, quantity),)
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key),
            place.project,
            place.owner,
            place.group,
        )
        group = await seeding.adding(TestSeedMainKernelGroupOf(image=image, slots=slots), session)
        environ = await seeding.adding(
            TestSeedKernelGroupEnvironOf(key=ENVIRON_KEY, value=ENVIRON_VALUE), group
        )
        group_slot = await seeding.adding(
            TestSeedKernelGroupResourceSlotOf(slot_name=slot_name, quantity=quantity), group
        )
        kernel = await seeding.adding_with_nested(
            TestSeedKernelOf(
                session=seeding.made(session),
                group=seeding.made(group),
                image=image,
                slots=slots,
            ),
            session,
        )
        caller: Laid[UserData]
        if self.granted is Granted.THE_PROJECT and self.permission is not Permission.READ:
            caller = await seeding.within(
                SomeoneGrantedSessionIn(
                    place.domain, place.project, self.permission, "session-updater"
                )
            )
        else:
            caller = await lay_a_caller_of(seeding, place, role=self.role, granted=self.granted)
        if self.beside_another_outside:
            await lay_the_same_shape(
                seeding,
                place,
                place.project,
                image=image,
                slots=slots,
                name_hint="beside-session",
            )
            await lay_the_same_shape(
                seeding,
                place,
                None,
                image=image,
                slots=slots,
                name_hint="outside-session",
            )
        return LaidSessionAndCaller(
            domain=seeding.made(place.domain),
            project=seeding.made(place.project),
            resource_group=seeding.made(place.group),
            owner=seeding.made(place.owner),
            image=image,
            session=seeding.made(session),
            group=seeding.made(group),
            environ=seeding.made(environ),
            group_slot=seeding.made(group_slot),
            kernel=seeding.made(kernel),
            caller=seeding.made(caller),
            slot_name=slot_name,
            quantity=quantity,
        )


async def lay_the_same_shape(
    seeding: Any,
    place: LaidPlace,
    project: Laid[ProjectData] | None,
    *,
    image: ImageData,
    slots: tuple[tuple[str, Decimal], ...],
    name_hint: str,
) -> None:
    """Lay one more session of the same shape, in ``project`` or in a new one."""
    if project is None:
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="outside-project"), place.domain, policy
        )
    session = await seeding.creating_from_three(
        TestSeedSession(access_key=place.access_key, name_hint=name_hint),
        project,
        place.owner,
        place.group,
    )
    group = await seeding.adding(TestSeedMainKernelGroupOf(image=image, slots=slots), session)
    await seeding.adding(
        TestSeedKernelGroupEnvironOf(key=ENVIRON_KEY, value=ENVIRON_VALUE), group
    )
    await seeding.adding(
        TestSeedKernelGroupResourceSlotOf(slot_name=slots[0][0], quantity=slots[0][1]), group
    )
    await seeding.adding_with_nested(
        TestSeedKernelOf(
            session=seeding.made(session),
            group=seeding.made(group),
            image=image,
            slots=slots,
        ),
        session,
    )


def allocation_dump(slot_name: str, quantity: Decimal) -> dict[str, Any]:
    """The allocation a waiting kernel holds: what it asked for, held, nothing allocated."""
    return {
        "requested": {"entries": [{"resource_type": slot_name, "quantity": quantity}]},
        "used": {"entries": [{"resource_type": slot_name, "quantity": quantity}]},
        "allocated": {"entries": []},
    }


def session_dump(laid: LaidSessionAndCaller) -> dict[str, Any]:
    """The whole session node the adapter builds from the row this scenario wrote."""
    session = laid.session
    return {
        "id": session.id,
        "entity_id": session.id,
        "image_ids": [],
        "domain_name": session.domain_name,
        "user_id": session.user_uuid,
        "project_id": session.group_id,
        "metadata": {
            "creation_id": session.creation_id,
            "name": session.name,
            "session_type": session.session_type.value,
            "access_key": str(session.access_key) if session.access_key else "",
            "cluster_mode": "SINGLE_NODE",
            "cluster_size": 1,
            "tier": 0,
            "priority": 0,
            "job_priority": 0,
            "is_preemptible": False,
            "tag": None,
        },
        "resource": {
            "allocation": allocation_dump(laid.slot_name, laid.quantity),
            "resource_group_name": session.resource_group_name,
            "session_group_id": session.session_group_id,
            "designated_agent_ids": None,
        },
        "lifecycle": {
            "status": "PENDING",
            "result": "undefined",
            "created_at": session.created_at,
            "terminated_at": None,
            "starts_at": None,
            "requested_starts_at": session.requested_starts_at,
            "batch_timeout": None,
        },
        "runtime": {
            "environ": None,
            "bootstrap_script": None,
            "startup_command": None,
            "callback_url": None,
        },
        "network": {
            "use_host_network": False,
            "network_type": "volatile",
            "network_id": None,
        },
        "replica_id": None,
    }


def _folded_kernel_status(status: Any) -> str:
    name = str(getattr(status, "name", ""))
    if name in ("PREPARING", "PULLING"):
        return "PREPARING"
    if name in ("CANCELLED", "BUILDING", "RESTARTING", "RESIZING", "SUSPENDED", "ERROR"):
        return "CANCELLED"
    return str(status.value)


def kernel_dump(kernel: KernelInfo, slot_name: str, quantity: Decimal) -> dict[str, Any]:
    """The whole kernel node the adapter builds from the kernel this scenario wrote."""
    return {
        "id": kernel.id,
        "field_id": kernel.id,
        "image_id": kernel.image.image_id,
        "kernel_group_id": kernel.kernel_group_id,
        "startup_command": kernel.runtime.startup_command,
        "session_info": {
            "session_id": UUID(kernel.session.session_id),
            "creation_id": kernel.session.creation_id,
            "name": kernel.session.name,
            "session_type": kernel.session.session_type.value,
        },
        "user_info": {
            "user_id": kernel.user_permission.user_uuid,
            "access_key": kernel.user_permission.access_key,
            "domain_name": kernel.user_permission.domain_name,
            "group_id": kernel.user_permission.group_id,
        },
        "network": {
            "service_ports": None,
            "preopen_ports": kernel.network.preopen_ports,
        },
        "cluster": {
            "cluster_role": kernel.cluster.cluster_role,
            "cluster_idx": kernel.cluster.cluster_idx,
            "local_rank": kernel.cluster.local_rank,
            "cluster_hostname": kernel.cluster.cluster_hostname,
        },
        "resource": {
            "agent_id": kernel.resource.agent,
            "resource_group_name": kernel.resource.resource_group,
            "container_id": kernel.resource.container_id,
            "allocation": allocation_dump(slot_name, quantity),
            "shares": {"entries": []},
            "resource_opts": None,
        },
        "lifecycle": {
            "status": _folded_kernel_status(kernel.lifecycle.status),
            "result": kernel.lifecycle.result.value,
            "created_at": kernel.lifecycle.created_at,
            "terminated_at": kernel.lifecycle.terminated_at,
            "starts_at": kernel.lifecycle.starts_at,
        },
    }


def kernel_group_dump(group: KernelGroupData) -> dict[str, Any]:
    """The whole kernel group node the adapter builds from the group this scenario wrote."""
    return {
        "id": group.id,
        "field_id": group.id,
        "session_id": group.session_id,
        "role": str(group.role),
        "image_id": group.image_id,
        "shmem": None,
        "startup_command": group.startup_command,
        "preopen_ports": group.preopen_ports,
        "requested_starts_at": group.requested_starts_at,
        "batch_timeout": group.batch_timeout_sec,
    }


def environ_dump(environ: KernelGroupEnvironData) -> dict[str, Any]:
    return {
        "id": environ.id,
        "field_id": environ.id,
        "kernel_group_id": environ.kernel_group_id,
        "key": environ.key,
        "value": environ.value,
    }


def group_slot_dump(slot: KernelGroupResourceSlotData) -> dict[str, Any]:
    return {
        "id": slot.id,
        "field_id": slot.id,
        "kernel_group_id": slot.kernel_group_id,
        "slot_name": str(slot.slot_name),
        "quantity": slot.quantity,
    }
