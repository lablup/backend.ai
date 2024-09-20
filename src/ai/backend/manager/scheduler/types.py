from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import (
    Any,
    Final,
    Generic,
    Mapping,
    MutableMapping,
    Optional,
    Self,
    Sequence,
    Set,
    TypeVar,
    override,
)

import attrs
import pydantic
import trafaret as t

from ai.backend.common.types import (
    AgentId,
    ArchName,
    KernelId,
    ResourceGroupID,
    ResourceSlot,
    SessionId,
    SlotName,
    SlotTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config import SharedConfig

from ..models import AgentRow, KernelRow, SessionRow
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
class KernelAgentBinding:
    kernel: KernelRow
    agent_alloc_ctx: AgentAllocationContext
    allocated_host_ports: Set[int]


@attrs.define(auto_attribs=True, slots=True)
class PredicateResult:
    passed: bool
    message: Optional[str] = None


class AbstractScheduler(ABC):
    """
    The interface for scheduling algorithms to choose a pending session to schedule.
    """

    sgroup_opts: ScalingGroupOpts  # sgroup-specific config
    config: Mapping[str, Any]  # scheduler-specific config

    def __init__(
        self,
        sgroup_opts: ScalingGroupOpts,
        config: Mapping[str, Any],
    ) -> None:
        self.sgroup_opts = sgroup_opts
        self.config = self.config_iv.check(config)

    @property
    @abstractmethod
    def config_iv(self) -> t.Dict:
        """
        The partial schema to extract configuration from the ``scaling_groups.scheduler_opts`` column.
        The returned ``t.Dict`` should set ``.allow_extra("*")`` to coexist with the agent-selector config.
        """
        raise NotImplementedError

    @staticmethod
    def prioritize(pending_sessions: Sequence[SessionRow]) -> tuple[int, list[SessionRow]]:
        """
        Filter the pending session list by the top priority among the observed priorities of the
        given pending sessions.
        """
        if not pending_sessions:
            return -1, []
        priorities = {s.priority for s in pending_sessions}
        assert len(priorities) > 0
        top_priority = max(priorities)
        return top_priority, [*filter(lambda s: s.priority == top_priority, pending_sessions)]

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
        raise NotImplementedError

    def update_allocation(
        self,
        scheduled_session_or_kernel: SessionRow | KernelRow,
    ) -> None:
        """
        An optional method to update internal states of the scheduler after a session is allocated
        and PASSED all predicate checks.

        This method is not called when any predicate check fails.
        """
        pass


class AbstractResourceGroupState(pydantic.BaseModel, ABC):
    @classmethod
    @abstractmethod
    def create_empty_state(cls) -> Self:
        raise NotImplementedError("must use a concrete subclass")


class RoundRobinState(pydantic.BaseModel):
    next_index: int = 0


class RRAgentSelectorState(AbstractResourceGroupState):
    roundrobin_states: dict[ArchName, RoundRobinState]

    @override
    @classmethod
    def create_empty_state(cls) -> Self:
        return cls(roundrobin_states={})


class NullAgentSelectorState(AbstractResourceGroupState):
    @override
    @classmethod
    def create_empty_state(cls) -> Self:
        return cls()


T_ResourceGroupState = TypeVar("T_ResourceGroupState", bound=AbstractResourceGroupState)


class AbstractAgentSelector(Generic[T_ResourceGroupState], ABC):
    """
    The interface for agent-selection logic to choose one or more agents to map with the given
    scheduled session.
    """

    sgroup_opts: ScalingGroupOpts  # sgroup-specific config
    config: Mapping[str, Any]  # agent-selector-specific config
    agent_selection_resource_priority: list[str]
    state_store: AbstractResourceGroupStateStore[T_ResourceGroupState]

    def __init__(
        self,
        sgroup_opts: ScalingGroupOpts,
        config: Mapping[str, Any],
        agent_selection_resource_priority: list[str],
        *,
        state_store: AbstractResourceGroupStateStore[T_ResourceGroupState],
    ) -> None:
        self.sgroup_opts = sgroup_opts
        self.config = self.config_iv.check(config)
        self.agent_selection_resource_priority = agent_selection_resource_priority
        self.state_store = state_store

    @property
    @abstractmethod
    def config_iv(self) -> t.Dict:
        """
        The partial schema to extract configuration from the ``scaling_groups.scheduler_opts`` column.
        The returned ``t.Dict`` should set ``.allow_extra("*")`` to coexist with the scheduler config.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_state_cls(cls) -> type[T_ResourceGroupState]:
        raise NotImplementedError()

    async def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
    ) -> Optional[AgentId]:
        """
        Assign an agent for the entire (single-node) session, only considering
        the total requested slots of the session.
        This method is used for both single-container sessions and
        single-node multi-container sessions.

        In single-node multi-container sessions, all sub-containers are spawned by
        slicing the assigned agent's resource.

        The default implementation is to simply call ``select_agent()`` method.
        """
        return await self.select_agent(agents, pending_session)

    async def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelRow,
    ) -> Optional[AgentId]:
        """
        Assign an agent for a kernel of a multi-node multi-container session.
        This may be called multiple times.

        The default implementation is to simply call ``select_agent()`` method.
        """
        return await self.select_agent(agents, pending_kernel)

    @abstractmethod
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Optional[AgentId]:
        """
        Select an agent for the pending session or kernel.
        """
        raise NotImplementedError


class AbstractResourceGroupStateStore(Generic[T_ResourceGroupState], ABC):
    """
    Store and load the state of the pending session scheduler and agent selector for each resource group.
    """

    def __init__(self, state_cls: type[T_ResourceGroupState]) -> None:
        self.state_cls = state_cls

    @abstractmethod
    async def load(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> T_ResourceGroupState:
        raise NotImplementedError

    @abstractmethod
    async def store(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
        state_value: T_ResourceGroupState,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reset(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> None:
        raise NotImplementedError


class DefaultResourceGroupStateStore(AbstractResourceGroupStateStore[T_ResourceGroupState]):
    """
    The default AgentSelector state store using the etcd
    """

    base_key: Final[str] = "resource-group-states"

    def __init__(self, state_cls: type[T_ResourceGroupState], shared_config: SharedConfig) -> None:
        super().__init__(state_cls)
        self.shared_config = shared_config

    @override
    async def load(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> T_ResourceGroupState:
        log.debug(
            "{}: load resource group state for {}", type(self).__qualname__, resource_group_name
        )
        if (
            raw_agent_selector_state := await self.shared_config.get_raw(
                f"{self.base_key}/{resource_group_name}/{state_name}",
            )
        ) is not None:
            return self.state_cls.model_validate_json(raw_agent_selector_state)
        return self.state_cls.create_empty_state()

    @override
    async def store(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
        state_value: T_ResourceGroupState,
    ) -> None:
        log.debug(
            "{}: store resource group state for {}", type(self).__qualname__, resource_group_name
        )
        await self.shared_config.etcd.put(
            f"{self.base_key}/{resource_group_name}/{state_name}",
            state_value.model_dump_json(),
        )

    @override
    async def reset(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> None:
        log.debug(
            "{}: reset resource group state for {}", type(self).__qualname__, resource_group_name
        )
        await self.shared_config.etcd.delete_prefix(
            f"{self.base_key}/{resource_group_name}/{state_name}",
        )


class InMemoryResourceGroupStateStore(AbstractResourceGroupStateStore[T_ResourceGroupState]):
    """
    An in-memory AgentSelector state store to use in test codes.
    This cannot be used for the actual dispatcher loop since the state is NOT preserved whenever the
    Scheduler and AgentSelector instances are recreated.
    """

    states: dict[tuple[ResourceGroupID, str], T_ResourceGroupState]

    def __init__(self, state_cls: type[T_ResourceGroupState]) -> None:
        super().__init__(state_cls)
        self.states = {}

    @override
    async def load(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> T_ResourceGroupState:
        log.debug(
            "{}: load resource group state for {}", type(self).__qualname__, resource_group_name
        )
        return self.states.get(
            (resource_group_name, state_name), self.state_cls.create_empty_state()
        )

    @override
    async def store(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
        state_value: T_ResourceGroupState,
    ) -> None:
        log.debug(
            "{}: store resource group state for {}", type(self).__qualname__, resource_group_name
        )
        self.states[(resource_group_name, state_name)] = state_value

    @override
    async def reset(
        self,
        resource_group_name: ResourceGroupID,
        state_name: str,
    ) -> None:
        log.debug(
            "{}: reset resource group state for {}", type(self).__qualname__, resource_group_name
        )
        del self.states[(resource_group_name, state_name)]
