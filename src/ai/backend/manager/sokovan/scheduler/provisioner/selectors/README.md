# Selectors

← [Back to Provisioner](../README.md) | [Scheduler](../../README.md)

## Overview

Selectors are plugins that select the optimal agent to run a session. A resource group can apply a different selection strategy, so agent selection fits objectives such as cluster utilization, high availability and load balancing.

**Key Responsibilities:**
- filtering the agents that satisfy the resource requirements
- selecting the optimal agent by the selection strategy
- multi-agent selection for multi-kernel sessions

## Architecture

```
┌───────────────────────────────────────┐
│     Session (Resource Requirements)   │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────┐
│           AgentSelector               │
│  1. Filter available agents           │
│  2. Apply selection strategy          │
│  3. Return optimal agent              │
└─────────────────┬─────────────────────┘
                  │
        ┌─────────┼─────────┬─────────┐
        │         │         │
        ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Concentrated│ │Dispersed│ │RoundRobin│
│(Bin-pack) │ │(Spread) │ │(Rotation)│
└──────────┘ └──────────┘ └──────────┘
```

## Core Classes

### AgentInfo

Data class with agent information.

```python
@dataclass
class AgentInfo:
    agent_id: AgentId
    available_slots: ResourceSlot    # Available resources
    occupied_slots: ResourceSlot     # Resources in use
    architecture: str                # CPU architecture
    # ... other attributes
```

### ResourceRequirements

Defines the resource requirements of a session.

```python
@dataclass
class ResourceRequirements:
    requested_slots: ResourceSlot    # Requested resources
    architecture: str | None         # Required architecture
    # ... other requirements
```

### AgentSelector (Abstract Base)

Base class of all Selectors.

```python
class AgentSelector(abc.ABC):
    @abc.abstractmethod
    def select(
        self,
        requirements: ResourceRequirements,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> AgentSelection:
        """
        Select the optimal agent that satisfies session requirements.

        Args:
            requirements: Session resource requirements
            agents: Candidate agent list
            criteria: Selection criteria settings

        Returns:
            Selected agent information

        Raises:
            NoAvailableAgentError: No agent satisfies conditions
        """
        pass
```

## Implementations

### ConcentratedSelector (Bin-packing)

Concentrates resources on specific agents to maximize utilization.

**Algorithm:**
1. Filter the agents that satisfy the resource requirements.
2. Prioritize the agents with the higher current occupancy.
3. When occupancy is equal, select the agent with the smaller total capacity.

**Advantages:**
- maximizes cluster utilization
- minimizes idle agents
- power and cost efficiency

**Disadvantages:**
- load concentration on specific agents
- larger impact when an agent fails

```
Agent Status:
  Agent A: [████████░░] 80% used
  Agent B: [████░░░░░░] 40% used
  Agent C: [░░░░░░░░░░] 0% used

Selection Result: Agent A (highest occupancy)
```

### DispersedSelector (Spreading)

Distributes resources across multiple agents for high availability.

**Algorithm:**
1. Filter the agents that satisfy the resource requirements.
2. Prioritize the agents with the lower current occupancy.
3. When occupancy is equal, select the agent with the larger total capacity.

**Advantages:**
- ensures high availability
- minimizes the impact of an agent failure
- balanced load distribution

**Disadvantages:**
- possible resource fragmentation
- lower cluster efficiency

```
Agent Status:
  Agent A: [████████░░] 80% used
  Agent B: [████░░░░░░] 40% used
  Agent C: [░░░░░░░░░░] 0% used

Selection Result: Agent C (lowest occupancy)
```

### RoundRobinSelector (Sequential Rotation)

Selects agents in rotation.

**Algorithm:**
1. Filter the agents that satisfy the resource requirements.
2. Select the next agent by the internal counter.
3. Increment the counter and cycle it.

**Advantages:**
- predictable distribution
- simple implementation
- equal request distribution

**Disadvantages:**
- does not consider the capacity differences of agents
- does not reflect dynamic load changes

```
Selection Order:
  Request 1 → Agent A
  Request 2 → Agent B
  Request 3 → Agent C
  Request 4 → Agent A (cycle)
```

## Exception Hierarchy

```
AgentSelectionError (base)
├── NoAvailableAgentError        # No available agents
├── NoCompatibleAgentError       # No compatible agents
├── ArchitectureIncompatibleError # Architecture mismatch
├── InsufficientResourcesError   # Insufficient resources
├── ContainerLimitExceededError  # Container count limit exceeded
└── TrackerCompatibilityError    # Tracker compatibility error
```

## Selection Process

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Sel as Selector
    participant Filter as Filter

    Sched->>Sel: select(requirements, agents)

    Sel->>Filter: filter_by_resources(agents)
    Note over Filter: Check CPU, Memory, GPU, etc.
    Filter-->>Sel: Resource-satisfying agents

    Sel->>Filter: filter_by_architecture(agents)
    Note over Filter: Check x86_64, aarch64, etc.
    Filter-->>Sel: Architecture-compatible agents

    alt No candidates
        Sel-->>Sched: raise NoAvailableAgentError
    else Candidates exist
        Note over Sel: Apply selection strategy
        Sel-->>Sched: AgentSelection
    end
```

## Multi-Kernel Session Support

Multi-kernel sessions (sessions composed of multiple kernels) need multi-agent selection.

```python
# Cluster session example
cluster_size = 4  # Cluster requiring 4 kernels

# Selector selects agent for each kernel
for kernel_idx in range(cluster_size):
    selection = selector.select(
        requirements=kernel_requirements[kernel_idx],
        agents=available_agents,
        criteria=criteria,
    )
    # Update selected agent's resource state
    tracker.allocate(selection.agent_id, kernel_requirements[kernel_idx])
```

## Writing Custom Selectors

### 1. Inherit AgentSelector

```python
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentSelector

class AffinitySelector(AgentSelector):
    """Image affinity-based selection"""

    def select(
        self,
        requirements: ResourceRequirements,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> AgentSelection:
        # 1. Basic filtering
        candidates = self._filter_by_resources(agents, requirements)

        if not candidates:
            raise NoAvailableAgentError()

        # 2. Prioritize agents that already have the image
        for agent in candidates:
            if requirements.image in agent.cached_images:
                return AgentSelection(agent_id=agent.agent_id)

        # 3. Select first candidate if none have image
        return AgentSelection(agent_id=candidates[0].agent_id)
```

### 2. Weight-based Selection

```python
class WeightedSelector(AgentSelector):
    """Multi-factor weight-based selection"""

    def __init__(
        self,
        utilization_weight: float = 0.4,
        affinity_weight: float = 0.3,
        locality_weight: float = 0.3,
    ):
        self._weights = {
            "utilization": utilization_weight,
            "affinity": affinity_weight,
            "locality": locality_weight,
        }

    def select(
        self,
        requirements: ResourceRequirements,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> AgentSelection:
        candidates = self._filter_by_resources(agents, requirements)

        if not candidates:
            raise NoAvailableAgentError()

        # Calculate score for each agent
        scored = [
            (agent, self._calculate_score(agent, requirements))
            for agent in candidates
        ]

        # Select agent with highest score
        best_agent = max(scored, key=lambda x: x[1])[0]
        return AgentSelection(agent_id=best_agent.agent_id)
```

## Configuration

Configure the Selector per resource group:

```python
scaling_group = {
    "name": "gpu-cluster",
    "scheduler": "fifo",
    "scheduler_opts": {
        "agent_selector": "concentrated",  # Selection strategy
    },
}
```

**Configuration Options:**

| Option | Description | Recommended Use Case |
|--------|-------------|---------------------|
| `concentrated` | bin-packing | GPU clusters, cost optimization |
| `dispersed` | spreading | high availability requirements, production |
| `roundrobin` | sequential rotation | development and test environments |

## Performance Considerations

- Agent filtering is O(n).
- Selection with sorting is O(n log n).
- Consider caching for large clusters.

## Related documents

- [Provisioner README](../README.md)
- [Scheduler README](../../README.md)
- [Allocators README](../allocators/README.md) - Post-selection allocation process
