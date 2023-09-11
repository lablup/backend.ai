from __future__ import annotations

import logging
import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Protocol,
    Sequence,
    Set,
)

import attrs
import sqlalchemy as sa
import trafaret as t
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.sql import ColumnElement, Select

from ai.backend.common.docker import ImageRef
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
    SlotName,
    SlotTypes,
    VFolderMount,
)

from ..defs import DEFAULT_ROLE
from ..models import AgentRow, KernelRow, SessionRow, kernels, keypairs
from ..models.scaling_group import ScalingGroupOpts
from ..registry import AgentRegistry

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))


def merge_resource(
    target: MutableMapping[str, Any],
    update: MutableMapping[str, Any],
) -> None:
    for k in update.keys():
        if k in target.keys():
            target[k] += update[k]
        else:
            target[k] = update[k]


@attrs.define(auto_attribs=True, slots=True)
class AgentAllocationContext:
    agent_id: Optional[AgentId]
    agent_addr: str
    scaling_group: str


@attrs.define(auto_attribs=True, slots=True)
class AgentContext:
    agent_id: AgentId
    agent_addr: str
    architecture: str
    scaling_group: str
    available_slots: ResourceSlot
    occupied_slots: ResourceSlot


@attrs.define(auto_attribs=True, slots=True)
class ScheduleDecision:
    agent_id: AgentId
    kernel_id: KernelId


@attrs.define(auto_attribs=True, slots=True)
class SchedulingContext:
    """
    Context for each scheduling decision.
    """

    registry: AgentRegistry
    known_slot_types: Mapping[SlotName, SlotTypes]


@attrs.define(auto_attribs=True, slots=True)
class ExistingSession:
    kernels: List[KernelInfo]
    access_key: AccessKey
    session_id: uuid.UUID
    session_type: SessionTypes
    session_name: str
    cluster_mode: ClusterMode
    cluster_size: int
    domain_name: str
    group_id: uuid.UUID
    scaling_group: str
    occupying_slots: ResourceSlot

    @classmethod
    def db_cols(cls) -> Set[ColumnElement]:
        return {
            kernels.c.id,
            kernels.c.status,
            kernels.c.access_key,
            kernels.c.session_id,
            kernels.c.session_type,
            kernels.c.session_name,
            kernels.c.cluster_mode,
            kernels.c.cluster_size,
            kernels.c.cluster_role,
            kernels.c.domain_name,
            kernels.c.group_id,
            kernels.c.scaling_group,
            kernels.c.occupied_slots,
        }

    @classmethod
    def base_query(cls) -> Select:
        return (
            sa.select(
                list(cls.db_cols() | KernelInfo.db_cols()),
            )
            .select_from(kernels)
            .order_by(kernels.c.created_at)
        )

    @classmethod
    def from_row(cls, row: Row) -> ExistingSession:
        return ExistingSession(
            kernels=[],
            access_key=row["access_key"],
            session_id=row["session_id"],
            session_type=row["session_type"],
            session_name=row["session_name"],
            cluster_mode=row["cluster_mode"],
            cluster_size=row["cluster_size"],
            domain_name=row["domain_name"],
            group_id=row["group_id"],
            scaling_group=row["scaling_group"],
            occupying_slots=ResourceSlot(),
        )

    @classmethod
    def from_rows(cls, rows: Sequence[Row]) -> List[ExistingSession]:
        items: Dict[str, ExistingSession] = {}
        for row in rows:
            if row["cluster_role"] == "main":
                items[row["session_id"]] = cls.from_row(row)
        for row in rows:
            session_id = row["session_id"]
            if session_id not in items:
                # In some cases, sub containers are still RUNNING
                # even though main container is TERMINATED.
                # To circumvent this edge case, we skip if main container
                # is not registered in `items`.
                continue
            session = items[session_id]
            session.kernels.append(KernelInfo.from_row(row))
            session.occupying_slots += row["occupied_slots"]  # type: ignore
        return list(items.values())


@attrs.define(auto_attribs=True, slots=True)
class PendingSession:
    """
    Context for individual session-related information used during scheduling.
    Resource parameters defined here should contain total amount of resources
    for all kernels in one session.
    """

    kernels: List[KernelInfo]
    access_key: AccessKey
    agent_id: AgentId
    agent_addr: str
    session_id: SessionId
    session_creation_id: str
    session_type: SessionTypes
    session_name: str
    cluster_mode: ClusterMode
    cluster_size: int
    domain_name: str
    group_id: uuid.UUID
    status_data: Mapping[str, Any]
    scaling_group: str
    resource_policy: str
    resource_opts: Mapping[str, Any]
    requested_slots: ResourceSlot
    target_sgroup_names: MutableSequence[str]
    environ: MutableMapping[str, str]
    vfolder_mounts: Sequence[VFolderMount]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: Optional[MutableMapping[str, Any]]
    preopen_ports: List[int]
    created_at: datetime
    use_host_network: bool

    @property
    def main_kernel_id(self) -> KernelId:
        for k in self.kernels:
            if k.cluster_role == DEFAULT_ROLE:
                return k.kernel_id
        raise RuntimeError("Unable to get the main kernel ID")

    @classmethod
    def db_cols(cls) -> Set[ColumnElement]:
        return {
            kernels.c.id,
            kernels.c.access_key,
            kernels.c.agent,
            kernels.c.agent_addr,
            kernels.c.session_creation_id,
            kernels.c.session_id,
            kernels.c.session_type,
            kernels.c.session_name,
            kernels.c.cluster_mode,
            kernels.c.cluster_size,
            kernels.c.domain_name,
            kernels.c.group_id,
            kernels.c.status_data,
            kernels.c.scaling_group,
            keypairs.c.resource_policy,
            kernels.c.occupied_slots,
            kernels.c.internal_data,
            kernels.c.resource_opts,
            kernels.c.environ,
            kernels.c.vfolder_mounts,
            kernels.c.bootstrap_script,
            kernels.c.startup_command,
            kernels.c.preopen_ports,
            kernels.c.created_at,
            kernels.c.use_host_network,
        }

    @classmethod
    def base_query(cls) -> Select:
        return (
            sa.select(
                list(cls.db_cols() | KernelInfo.db_cols()),
            )
            .select_from(
                sa.join(
                    kernels,
                    keypairs,
                    keypairs.c.access_key == kernels.c.access_key,
                )
            )
            .order_by(kernels.c.created_at)
        )

    @classmethod
    def from_row(cls, row: Row) -> PendingSession:
        return cls(
            kernels=[],
            access_key=row["access_key"],
            agent_id=row["agent"],
            agent_addr=row["agent_addr"],
            session_creation_id=row["session_creation_id"],
            session_id=row["session_id"],
            session_type=row["session_type"],
            session_name=row["session_name"],
            cluster_mode=row["cluster_mode"],
            cluster_size=row["cluster_size"],
            domain_name=row["domain_name"],
            group_id=row["group_id"],
            status_data=row["status_data"],
            scaling_group=row["scaling_group"],
            resource_policy=row["resource_policy"],
            resource_opts={},
            requested_slots=ResourceSlot(),
            internal_data=row["internal_data"],
            target_sgroup_names=[],
            environ={k: v for k, v in map(lambda s: s.split("=", maxsplit=1), row["environ"])},
            vfolder_mounts=row["vfolder_mounts"],
            bootstrap_script=row["bootstrap_script"],
            startup_command=row["startup_command"],
            preopen_ports=row["preopen_ports"],
            created_at=row["created_at"],
            use_host_network=row["use_host_network"],
        )

    @classmethod
    def from_rows(cls, rows: Sequence[Row]) -> List[PendingSession]:
        items: Dict[SessionId, PendingSession] = {}
        for row in rows:
            if row["cluster_role"] == "main":
                items[row["session_id"]] = cls.from_row(row)
        for row in rows:
            session = items[row["session_id"]]
            session.kernels.append(KernelInfo.from_row(row))
            session.requested_slots += row["occupied_slots"]  # type: ignore
            merge_resource(session.resource_opts, row["resource_opts"])  # type: ignore
        return list(items.values())


@attrs.define(auto_attribs=True, slots=True)
class KernelInfo:
    """
    Representing invididual kernel info.
    Resource parameters defined here should contain single value of resource
    for each kernel.
    """

    kernel_id: KernelId
    session_id: SessionId
    access_key: AccessKey
    agent_id: AgentId
    agent_addr: str
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str
    image_ref: ImageRef
    resource_opts: Mapping[str, Any]
    requested_slots: ResourceSlot
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    created_at: datetime

    def __str__(self):
        return f"{self.kernel_id}#{self.cluster_role}{self.cluster_idx}"

    @classmethod
    def db_cols(cls) -> Set[ColumnElement]:
        return {
            kernels.c.id,
            kernels.c.session_id,
            kernels.c.access_key,
            kernels.c.agent,  # for scheduled kernels
            kernels.c.agent_addr,  # for scheduled kernels
            kernels.c.cluster_role,
            kernels.c.cluster_idx,
            kernels.c.local_rank,
            kernels.c.cluster_hostname,
            kernels.c.image,
            kernels.c.architecture,
            kernels.c.registry,
            kernels.c.resource_opts,
            kernels.c.occupied_slots,
            kernels.c.bootstrap_script,
            kernels.c.startup_command,
            kernels.c.created_at,
        }

    @classmethod
    def from_row(cls, row: Row) -> KernelInfo:
        return cls(
            kernel_id=row["id"],
            session_id=row["session_id"],
            access_key=row["access_key"],
            agent_id=row["agent"],
            agent_addr=row["agent_addr"],
            cluster_role=row["cluster_role"],
            cluster_idx=row["cluster_idx"],
            local_rank=row["local_rank"],
            cluster_hostname=row["cluster_hostname"],
            image_ref=ImageRef(row["image"], [row["registry"]], row["architecture"]),
            resource_opts=row["resource_opts"],
            requested_slots=row["occupied_slots"],
            bootstrap_script=row["bootstrap_script"],
            startup_command=row["startup_command"],
            created_at=row["created_at"],
        )


@attrs.define(auto_attribs=True, slots=True)
class KernelAgentBinding:
    kernel: KernelRow
    agent_alloc_ctx: AgentAllocationContext
    allocated_host_ports: Set[int]


@attrs.define(auto_attribs=True, slots=True)
class PredicateResult:
    passed: bool
    message: Optional[str] = None


class SchedulingPredicate(Protocol):
    async def __call__(
        self,
        db_conn: SAConnection,
        sched_ctx: SchedulingContext,
        sess_ctx: PendingSession,
    ) -> PredicateResult: ...


class AbstractScheduler(metaclass=ABCMeta):
    """
    Interface for scheduling algorithms where the
    ``schedule()`` method is a pure function.
    """

    sgroup_opts: ScalingGroupOpts  # sgroup-specific config
    config: Mapping[str, Any]  # scheduler-specific config
    config_iv: t.Dict

    def __init__(self, sgroup_opts: ScalingGroupOpts, config: Mapping[str, Any]) -> None:
        self.sgroup_opts = sgroup_opts
        self.config = self.config_iv.check(config)

    @abstractmethod
    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        """
        Pick a session to try schedule.
        This is where the queueing semantics is implemented such as prioritization.
        """
        return None

    @abstractmethod
    def assign_agent_for_session(
        self,
        possible_agents: Sequence[AgentRow],
        pending_session: SessionRow,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        """
        Assign an agent for the entire session, only considering the total requested
        slots of the session.  This is used for both single-container sessions and
        single-node multi-container sessions.

        In single-node multi-container sessions, all sub-containers are spawned by
        slicing the assigned agent's resource.
        """
        return None

    @abstractmethod
    def assign_agent_for_kernel(
        self,
        possible_agents: Sequence[AgentRow],
        pending_kernel: KernelInfo,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        """
        Assign an agent for a kernel of the session.
        This may be called multiple times for multi-node multi-container sessions.
        """
        return None
