---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-01-13
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# Fair Share Scheduler

## Related Issues

- JIRA Epic: [BA-3060](https://lablup.atlassian.net/browse/BA-3060) - Implement Fair Share Scheduler for Sokovan
- JIRA Stories:
  - [BA-3812](https://lablup.atlassian.net/browse/BA-3812) - Resource Usage tables
  - [BA-3063](https://lablup.atlassian.net/browse/BA-3063) - Fair Share calculation service
  - [BA-3064](https://lablup.atlassian.net/browse/BA-3064) - FairShareSequencer plugin
  - [BA-3860](https://lablup.atlassian.net/browse/BA-3860) - BEP document

## Motivation

### Current Limitations of DRF (Dominant Resource Fairness)

The current DRFSequencer in the Sokovan scheduler determines priority based solely on **currently occupied resources**:

```python
# DRFSequencer - Only considers currently occupied resources
for access_key, occupancy in system_snapshot.resource_occupancy.by_keypair.items():
    dominant_share = self._calculate_dominant_share(
        occupancy.occupied_slots,  # Only considers currently occupied resources
        system_snapshot.total_capacity
    )
```

Problems with this approach:

| Scenario | User A | User B | DRF Result |
|---------|--------|--------|----------|
| Current occupancy | 10% | 10% | Equal priority |
| Yesterday's usage | 10% | 90% | **Not considered** |
| Fairness | Appropriate | **Unfair** | DRF cannot distinguish |

### The Need for Historical Fair Share

**Time-based Fair Share** is a standard scheduling policy used in HPC (High-Performance Computing) environments:

1. **Burst Abuse Prevention**: Give priority to users who have used fewer resources over users who have used more in the past
2. **Time Decay**: Apply higher weights to recent usage to reduce the impact of old usage history
3. **Industry Standard**: Adopted by major HPC schedulers such as Slurm, PBS, LSF

### Use Case Example

```
Scenario: GPU cluster, 2 users

Day 1-6:
  - User A: Uses GPU 4 hours daily (total 24 hours)
  - User B: No usage (total 0 hours)

Day 7 (today):
  - Current occupancy: Both at 0%
  - Both User A and User B submit new jobs

DRF Result: Equal priority (same current occupancy)
Fair Share Result: User B gets priority (less past usage)
```

## Current Design

### WorkloadSequencer Interface

```python
# src/ai/backend/manager/sokovan/scheduler/provisioner/sequencers/sequencer.py
class WorkloadSequencer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the sequencer name for predicates."""

    @abstractmethod
    def success_message(self) -> str:
        """Return a message describing successful sequencing."""

    @abstractmethod
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """Sequence workloads based on the system snapshot."""
```

### Current DRFSequencer Implementation

```python
# src/ai/backend/manager/sokovan/scheduler/provisioner/sequencers/drf.py
class DRFSequencer(WorkloadSequencer):
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        user_dominant_shares: dict[AccessKey, Decimal] = defaultdict(lambda: Decimal(0))

        # Calculate dominant share from currently occupied resources
        for access_key, occupancy in system_snapshot.resource_occupancy.by_keypair.items():
            dominant_share = self._calculate_dominant_share(
                occupancy.occupied_slots, system_snapshot.total_capacity
            )
            user_dominant_shares[access_key] = dominant_share

        # Sort by dominant share in ascending order (lower = higher priority)
        return sorted(workloads, key=lambda w: user_dominant_shares[w.access_key])
```

### SystemSnapshot Structure

```python
@dataclass
class SystemSnapshot:
    total_capacity: ResourceSlot                    # Total cluster capacity
    resource_occupancy: ResourceOccupancySnapshot   # Current resource occupancy state
    resource_policy: ResourcePolicySnapshot         # Resource policy
    concurrency: ConcurrencySnapshot                # Concurrent session state
    pending_sessions: PendingSessionSnapshot        # Pending sessions
    session_dependencies: SessionDependencySnapshot # Session dependencies

@dataclass
class ResourceOccupancySnapshot:
    by_keypair: MutableMapping[AccessKey, KeypairOccupancy]  # Per-user occupancy
    by_user: MutableMapping[UUID, ResourceSlot]
    by_group: MutableMapping[UUID, ResourceSlot]
    by_domain: MutableMapping[str, ResourceSlot]
    by_agent: MutableMapping[AgentId, AgentOccupancy]
```

### Sequencer Registration Method

```python
# src/ai/backend/manager/sokovan/scheduler/provisioner/provisioner.py
@classmethod
def _make_sequencer_pool(cls) -> Mapping[str, WorkloadSequencer]:
    pool: dict[str, WorkloadSequencer] = defaultdict(DRFSequencer)
    pool["fifo"] = FIFOSequencer()
    pool["lifo"] = LIFOSequencer()
    pool["drf"] = DRFSequencer()
    return pool
```

## Proposed Design

### 1. Fair Share Algorithm

#### Slurm-style Half-life Decay Formula

**Fair Share Factor Calculation:**
```
F = 2^(-UH / S)

Where:
- F: Fair Share Factor (0.0 ~ 1.0, higher = higher priority)
- UH: Effective Historical Usage (cumulative usage with time decay applied)
- S: Share Allocation (allocated resource ratio, default 1.0)
```

**Effective Historical Usage Calculation:**
```
UH = U_current + (D × U_last) + (D² × U_prev) + (D³ × U_prev2) + ...

Where:
- U_i: Resource usage for the i-th period (processor × seconds)
- D: Decay Factor = 2^(-bucket_unit / half_life)
- bucket_unit: Aggregation unit (e.g., 1 day)
- half_life: Half-life (default: 7 days)
```

#### Decay Calculation Method: Flat (Fixed)

**Comparison of Two Methods:**

| Method | Description | Complexity | Slurm Compatible |
|------|------|--------|------------|
| **Flat** | Same weight per half-life period | O(periods) | ✓ |
| Continuous | Daily continuous decay | O(days) | ✗ |

**Using Flat Method Only (Slurm Compatible):**

The actual scheduling result difference between Continuous and Flat methods is minimal, but Flat computation is more efficient.
Therefore, we implement **only the Flat method** and do not make it configurable.

```
Period 0 (0-7 days):    Weight 1.0
Period 1 (7-14 days):   Weight 0.5
Period 2 (14-21 days):  Weight 0.25
Period 3 (21-28 days):  Weight 0.125
```

**Time Decay Visualization:**
```
Weight
   │
1.0├────●━━━━━━━━┓ Period 0
   │             ┃
0.5├──────●━━━━━━┫ Period 1
   │             ┃
0.25├────────●━━━┫ Period 2
   │             ┃
0.125├───────────●┛ Period 3
   │
   └──────────────────────► Time (days)
      0    7    14    21

━━ Flat method (step-wise, per half-life period)
```

**Reasons for Choosing Flat Method:**
- Same method as Slurm for industry standard compatibility
- Computationally efficient (calculations for 28 days: 28 → 4)
- Minimal difference in actual scheduling results compared to Continuous
- Simplified implementation and debugging

#### Multi-Resource Normalization

**Problem: Multiple Resource Types**

Backend.AI manages multiple resource types (CPU, memory, GPU, etc.), so the Fair Share calculation
must handle different resource dimensions.

**Approaches Considered:**

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **SLURM TRESBillingWeights** | Combine resources into single billing unit | Simple computation | Requires careful weight tuning |
| **Usage-based Normalization** | `UserUsage / TotalClusterUsage` | Industry standard (SLURM) | Unfair when cluster underutilized |
| **Capacity-based Normalization** | `UserUsage / ClusterCapacity` | Fair regardless of utilization | Requires capacity tracking |

**Chosen Approach: Capacity-based Per-Resource Normalization**

```
normalized_usage = Σ((usage[r] / capacity[r]) × weight[r]) / Σ(weight[r])

Where:
- r: Each resource type (cpu, mem, cuda.device, etc.)
- usage[r]: User's resource usage for type r (resource-seconds)
- capacity[r]: Cluster capacity for type r (resource-seconds)
- weight[r]: Resource weight for type r (from scheduler_opts.resource_weights)

IMPORTANT - Unit Consistency:
Both usage and capacity MUST be in the same unit (resource-seconds).
- usage: Accumulated from kernel usage records (e.g., 3600 GPU-seconds = 1 GPU-hour)
- capacity: agent.available_slots × period_duration_seconds
  (e.g., 8 GPUs × 28 days × 86400 sec/day = 19,353,600 GPU-seconds)

DO NOT mix resource-seconds (usage) with raw resource units (capacity).
This would cause incorrect ratios (e.g., 3,600,000 / 8 = 450,000 instead of 0.186).
```

**Why Capacity-based is Better Than Usage-based:**

```
Scenario: Cluster with 100 GPU capacity

Usage-based (SLURM style):
- User A is the only user, used 10 GPU-hours
- normalized_usage = 10 / 10 = 100% (A has 100% of total usage!)
- Problem: Small usage gets 100% penalty when cluster underutilized

Capacity-based (Backend.AI approach):
- User A used 10 GPU-hours, cluster capacity = 100
- normalized_usage = 10 / 100 = 10%
- Fair: Usage is correctly proportional to available capacity
```

**Resource Weight Configuration:**

Resource weights are configured in `resource_groups.scheduler_opts`:

```python
# scheduler_opts
{
    "resource_weights": {
        "cpu": 1.0,
        "mem": 1.0,
        "cuda.device": 10.0,  # GPU weighted 10x
        "cuda.shares": 1.0,
    }
}
```

**Calculation Example (1-day period):**

```
Cluster capacity (resource-seconds for 1 day = 86400 seconds):
- cpu: 100 cores × 86400 sec = 8,640,000 cpu-seconds
- mem: 1000 GB × 86400 sec = 86,400,000 mem-seconds
- cuda.device: 8 GPUs × 86400 sec = 691,200 GPU-seconds

User's usage (used 4 GPUs for 4 hours):
- cpu: 20 cores × 4 hours × 3600 sec = 288,000 cpu-seconds
- mem: 200 GB × 4 hours × 3600 sec = 2,880,000 mem-seconds
- cuda.device: 4 GPUs × 4 hours × 3600 sec = 57,600 GPU-seconds

Resource weights: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}

Per-resource ratio (both in resource-seconds):
- cpu: 288,000 / 8,640,000 = 0.0333 (3.33%)
- mem: 2,880,000 / 86,400,000 = 0.0333 (3.33%)
- cuda.device: 57,600 / 691,200 = 0.0833 (8.33%)

Weighted average:
normalized_usage = (0.0333×1.0 + 0.0333×1.0 + 0.0833×10.0) / (1.0 + 1.0 + 10.0)
                 = (0.0333 + 0.0333 + 0.833) / 12.0
                 = 0.8996 / 12.0
                 = 0.075 (7.5%)
```

**Edge Case: Zero Capacity**

When capacity for a resource is zero or unavailable (e.g., all agents offline):

```python
def calculate_normalized_usage(
    usage: ResourceSlot,
    capacity: ResourceSlot,
    weights: ResourceSlot,
) -> Decimal:
    weighted_sum = Decimal(0)
    weight_sum = Decimal(0)

    for resource_type, weight in weights.items():
        cap = capacity.get(resource_type, Decimal(0))
        if cap <= 0:
            # Skip this resource - capacity unavailable
            continue

        use = usage.get(resource_type, Decimal(0))
        ratio = Decimal(use) / Decimal(cap)
        weighted_sum += ratio * Decimal(weight)
        weight_sum += Decimal(weight)

    if weight_sum == 0:
        # No valid resources to calculate - return 0 (new user priority)
        return Decimal(0)

    return weighted_sum / weight_sum
```

**Capacity Tracking Strategy:**

To ensure stable Fair Share calculation when cluster capacity changes (e.g., agents added/removed),
each Usage Bucket stores a **capacity_snapshot** at creation time:

```
Day 1: Cluster has 100 GPUs
- User A's bucket: usage=10, capacity_snapshot=100
- Usage ratio = 10/100 = 10%

Day 2: 20 GPUs removed (maintenance)
- New bucket: usage=5, capacity_snapshot=80
- Usage ratio = 5/80 = 6.25%
- Day 1 bucket unchanged: still 10/100 = 10%

Result: Historical ratios remain stable despite capacity changes
```

### 2. 2-Tier Storage Architecture

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tier 1: Source of Truth                       │
│                    kernel_usage_records table                    │
│  ┌──────────┬───────────┬───────────┬──────────────┬──────────┐ │
│  │kernel_id │ user_uuid │ resources │ period_start │period_end│ │
│  └──────────┴───────────┴───────────┴──────────────┴──────────┘ │
│  - Per-period slice kernel usage records (raw data)              │
│  - Retained for lookback_days (used when decay recalculation)    │
│  - Each record represents usage for a specific period            │
│    (period_start ~ period_end)                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Batch aggregation (5-minute cycle)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Tier 2: Usage Buckets (period-based cache)       │
│  domain_usage_buckets / project_usage_buckets / user_usage_buckets │
│  ┌───────────┬──────────────┬─────────────┬───────────────────┐ │
│  │ entity_id │ period_start │ period_end  │ resource_usage    │ │
│  └───────────┴──────────────┴─────────────┴───────────────────┘ │
│  - Per-decay-unit period aggregation cache (separated by tier)   │
│  - Recalculated from kernel_usage_records when decay config changes │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ decay-applied summation
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               Tier 3: Fair Shares (state summary, user visibility) │
│    domain_fair_shares / project_fair_shares / user_fair_shares    │
│  ┌───────────┬────────┬───────────────────┬────────────────────┐ │
│  │ entity_id │ weight │ total_decayed_usage │ fair_share_factor │ │
│  └───────────┴────────┴───────────────────┴────────────────────┘ │
│  - weight: Admin-configured value                                │
│  - total_decayed_usage: Decay-applied sum of all buckets         │
│  - fair_share_factor: F = 2^(-UH/S) calculation result           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Scheduling time (2-second cycle)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FairShareSequencer                           │
│  1. Collect (user_uuid, project_id) pairs from workloads         │
│  2. Read cached factors from user_fair_shares table              │
│  3. Sort pending sessions by fair_share_factor (descending)      │
└─────────────────────────────────────────────────────────────────┘
```

#### Storage Role Separation

| Table | Role | Retention Period | Recalculation |
|--------|------|-----------|--------|
| kernel_usage_records | Raw data (Source of Truth) | lookback_days | Not required |
| *_usage_buckets | Period-based aggregation cache | By decay_unit | When decay config changes |
| *_fair_shares | State summary + weight config | Permanent | Updated by batch |

#### Performance Separation Strategy

| Operation | Cycle | Content | Complexity |
|------|------|------|--------|
| Scheduling | 2 sec | Read from fair_shares table (cached factor) | O(pending_users) |
| Batch aggregation | 5 min | raw → buckets → fair_shares update | O(kernels) |
| Cache recalculation | On config change | Regenerate all buckets from raw | O(records) |

### 3. Database Schema

#### KernelRow Extension

Add `last_usage_recorded_at` column to track the last usage measurement time:

```python
# In KernelRow (existing table)
class KernelRow(Base):
    # ... existing columns ...

    # Last usage measurement timestamp (for batch aggregation)
    last_usage_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None,
        comment="Timestamp of last usage record creation. "
                "Used by UsageAggregationService to determine slice start time."
    )
```

#### kernel_usage_records Table

Raw data table storing per-period usage slices for kernels.

```python
class KernelUsageRecordRow(Base):
    """Per-period kernel resource usage records (raw data).

    Each record represents kernel resource usage during a specific
    period (period_start ~ period_end). Generated in 5-minute intervals
    by batch aggregation.

    Tracks resource_usage: Allocated resources × time (for Fair Share calculation).
    Actual measured usage is available via Prometheus metrics (not stored in DB).
    """

    __tablename__ = "kernel_usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    kernel_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False)

    # User identification (user_uuid based, access_key not used)
    user_uuid: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_group: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Period slice information
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Allocated resource usage for the period (allocated × seconds)
    # Used for Fair Share calculation
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot()
    )

    # Relationships (Optional since referenced entities can be deleted)
    kernel: Mapped[KernelRow | None] = relationship("KernelRow", back_populates="usage_records")
    session: Mapped[SessionRow | None] = relationship("SessionRow")
    user: Mapped[UserRow | None] = relationship("UserRow")
    project: Mapped[GroupRow | None] = relationship("GroupRow")
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    # Composite indexes
    __table_args__ = (
        Index("ix_kernel_usage_rg_period", "resource_group", "period_start"),
        Index("ix_kernel_usage_user_period", "user_uuid", "period_start"),
    )
```

**Period Slice Example:**
```
Kernel K1 (started: 10:00, terminated: 10:23)
├── Record 1: period_start=10:00, period_end=10:05 (5 min)
├── Record 2: period_start=10:05, period_end=10:10 (5 min)
├── Record 3: period_start=10:10, period_end=10:15 (5 min)
├── Record 4: period_start=10:15, period_end=10:20 (5 min)
└── Record 5: period_start=10:20, period_end=10:23 (3 min, terminated)
```

**Resource Usage Normalization (Resource-Seconds):**

`resource_usage` is stored in **resource amount × duration (seconds)** units.
This normalization allows simple summation across kernels with different time spans.

```python
def _calculate_usage(
    occupied_slots: ResourceSlot,  # Kernel's occupied resources
    period_start: datetime,
    period_end: datetime,
) -> ResourceSlot:
    """Normalize to resource × time.

    Duration is calculated in seconds, maintaining microsecond precision.
    (datetime.timedelta.total_seconds() returns a float including microseconds)
    """
    duration_seconds = (period_end - period_start).total_seconds()
    return ResourceSlot({
        key: value * duration_seconds
        for key, value in occupied_slots.items()
    })
```

```
Example: Kernel K1 (10:00~10:30, 1800 seconds), occupied_slots = {"cpu": 5, "mem": 10, "cuda.shares": 1}

resource_usage = {
    "cpu": 5 × 1800 = 9,000 cpu-seconds,
    "mem": 10 × 1800 = 18,000 mem-seconds,
    "cuda.shares": 1 × 1800 = 1,800 gpu-seconds
}
```

**Multiple Kernel Summation Example:**
```
User A's kernels (2026-01-13):
├── Kernel 1 (10:00~10:30): {"cpu": 9000, "mem": 18000, "cuda.shares": 1800}
├── Kernel 2 (10:15~10:45): {"cpu": 3600, "mem": 5400, "cuda.shares": 5400}
└── Kernel 3 (14:00~15:00): {"cpu": 7200, "mem": 3600}

Daily sum (time-span independent, simple sum):
{"cpu": 19800, "mem": 27000, "cuda.shares": 7200}
```

**Billing Conversion:**
- CPU-hours: `cpu-seconds / 3600`
- GPU-hours: `cuda.shares-seconds / 3600`

#### Usage Buckets Tables (Per-tier Aggregation)

Usage cache aggregated per decay-unit period. Consists of 3 separate tables per tier.
Recalculated from kernel_usage_records when decay configuration changes.

**Tier Structure:**
```
DomainUsageBucket     (domain_name, resource_group, period)
    └── ProjectUsageBucket  (project_id, domain_name, resource_group, period)
            └── UserUsageBucket   (user_uuid, project_id, domain_name, resource_group, period)
```

**Note:** A User can belong to multiple Projects, so UserUsageBucket is uniquely identified
by the `(user_uuid, project_id, domain_name, resource_group, period_start)` combination.

##### domain_usage_buckets Table

```python
class DomainUsageBucketRow(Base):
    """Per-domain period-based resource usage aggregation.

    Cache summing all Project/User usage within the domain.
    Tracks both allocated and measured usage for multi-purpose use.
    """

    __tablename__ = "domain_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Aggregated allocated resource usage (resource-seconds unit)
    # Used for Fair Share calculation
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot()
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource group capacity at bucket period. "
                "Sum of agent.available_slots for calculating usage ratio."
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    domain: Mapped[DomainRow | None] = relationship("DomainRow", back_populates="usage_buckets")

    __table_args__ = (
        UniqueConstraint(
            "domain_name", "resource_group", "period_start",
            name="uq_domain_usage_bucket"
        ),
        Index("ix_domain_usage_bucket_lookup", "domain_name", "resource_group", "period_start"),
    )
```

##### project_usage_buckets Table

```python
class ProjectUsageBucketRow(Base):
    """Per-project period-based resource usage aggregation.

    Cache summing all User usage within the project.
    """

    __tablename__ = "project_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Aggregated allocated resource usage (resource-seconds unit)
    # Used for Fair Share calculation
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot()
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource group capacity at bucket period. "
                "Sum of agent.available_slots for calculating usage ratio."
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    project: Mapped[GroupRow | None] = relationship("GroupRow", back_populates="usage_buckets")
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    __table_args__ = (
        UniqueConstraint(
            "project_id", "resource_group", "period_start",
            name="uq_project_usage_bucket"
        ),
        Index("ix_project_usage_bucket_lookup", "project_id", "resource_group", "period_start"),
    )
```

##### user_usage_buckets Table

```python
class UserUsageBucketRow(Base):
    """Per-user period-based resource usage aggregation (computation cache).

    Cache aggregating raw data from kernel_usage_records per decay_unit period.
    Since a User can belong to multiple Projects, distinguished by (user_uuid, project_id) combination.
    """

    __tablename__ = "user_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )

    # User identification (user_uuid + project_id + domain_name combination)
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Aggregated allocated resource usage (resource-seconds unit)
    # Used for Fair Share calculation
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot()
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource group capacity at bucket period. "
                "Sum of agent.available_slots for calculating usage ratio."
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[UserRow | None] = relationship("UserRow", back_populates="usage_buckets")
    project: Mapped[GroupRow | None] = relationship("GroupRow")
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    __table_args__ = (
        UniqueConstraint(
            "user_uuid", "project_id", "resource_group", "period_start",
            name="uq_user_usage_bucket"
        ),
        Index("ix_user_usage_bucket_lookup", "user_uuid", "project_id", "resource_group", "period_start"),
    )
```

**Bucket Update Strategy (Mutable + period_end Extension):**

After creation, buckets have `period_end` progressively extended until exceeding `decay_unit_days`, when a new bucket is created.

```
When decay_unit_days = 7:

Day 1 (Jan 6):
  No bucket → INSERT (period_start=Jan 6, period_end=Jan 6)

Day 2 (Jan 7):
  Existing bucket → UPDATE period_end=Jan 7, accumulate resource_usage
  (Jan 7 - Jan 6 = 1 day < 7 days → keep same bucket)

Day 3~7:
  Continue UPDATE period_end, accumulate resource_usage

Day 7 (Jan 12):
  UPDATE period_end=Jan 12
  (Jan 12 - Jan 6 = 6 days < 7 days → keep same bucket)

Day 8 (Jan 13):
  Jan 13 - Jan 6 = 7 days ≥ decay_unit_days → exceeded!
  → INSERT new bucket (period_start=Jan 13, period_end=Jan 13)
  → Previous bucket [Jan 6 ~ Jan 12] becomes effectively immutable
```

**Invariant**: `period_end - period_start < decay_unit_days`

**Bucket States:**
- `period_end - period_start < decay_unit_days`: Currently active bucket (being updated)
- `period_end - period_start >= decay_unit_days - 1`: Completed bucket (no more updates)

**Cache Recalculation Conditions:**
- When `decay_unit_days` configuration changes (bucket boundary change)
- When data integrity issues occur

### 4. Period Slice Generation Pattern

#### Slice Generation Method

The batch aggregation service periodically generates slices for running kernels and recently terminated kernels.
Terminated kernels are also processed based on `terminated_at` during batch operations.

```
┌─────────────────────────────────────────────────────────────────┐
│  Batch Aggregation Target Kernels:                               │
│  1. Running kernels (status IN RUNNING_STATUSES)                 │
│  2. Kernels terminated after the last slice                      │
│     (terminated_at > last_slice_end)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼ Batch aggregation
┌─────────────────────────────────────────────────────────────────┐
│  For each kernel:                                                │
│                                                                  │
│  1. Determine slice period                                       │
│     period_start = last_slice_end OR started_at                  │
│     period_end = terminated_at OR now                            │
│                                                                  │
│  2. Create slice (only if period_end > period_start)             │
│     INSERT INTO kernel_usage_records (...)                       │
│                                                                  │
│  3. Update cursor                                                │
│     kernels.last_slice_end = period_end                          │
└─────────────────────────────────────────────────────────────────┘
```

#### Handling Terminated Kernels

**Separate Event Handler Not Required:** When the Coordinator changes kernel status, only setting `terminated_at`
is sufficient, and the final slice is automatically created in the next batch aggregation.

```python
# When kernel terminates in Coordinator (existing logic)
kernel.status = KernelStatus.TERMINATED
kernel.terminated_at = datetime.now(timezone.utc)
# Do not change last_slice_end → handled by batch

# Automatically processed during batch aggregation
# Kernels with terminated_at > last_slice_end → final slice created
```

#### Slice Gap Strategy

**Principle: Allow Gaps + Configuration-based Handling**

Perfect recovery during server downtime is impossible, and Fair Share is about relative priority,
so minor errors are acceptable. Gap handling policy is controlled by configuration (`gap_policy`).

| Setting | Description | Behavior |
|--------|------|------|
| `interpolate` | Assume server was running and interpolate | Create single slice for entire gap period |
| `ignore` | Exclude unknown period from aggregation | Treat gap period as 0 |

```
Normal operation:
├── 10:00-10:05 (5 min)
├── 10:05-10:10 (5 min)
├── 10:10-10:15 (5 min)
└── 10:15-10:20 (5 min)

After server downtime recovery (10:05 ~ 10:25 downtime):
├── 10:00-10:05 (5 min) - created before downtime
│
├── [interpolate selected]
│   └── 10:05-10:30 (25 min) - created as single large slice after recovery (assumes server was running)
│
└── [ignore selected]
    └── 10:25-10:30 (5 min) - created from recovery point only (ignore downtime period)

Long-term downtime (2+ days):
- interpolate: 2 days of usage concentrated in one bucket (possible distortion, limited by max_gap_hours)
- ignore: 2 days of usage lost (minimal impact on fairness)
```

**Slice Creation Timing:**
- **Trigger-based**: Slices created based on when batch scheduler executes
- Not exact 5-minute intervals, but aggregating period since last slice at batch execution time
- This may result in slight variations like 4 min 55 sec ~ 5 min 5 sec (acceptable)

**Gap Detection on Server Restart:**

Large gaps can occur between the last slice and current time when server restarts.
To detect this, use `server_started_at` (server start time).

```python
# On batch aggregation service start
class UsageAggregationService:
    def __init__(self, ...):
        self._server_started_at = datetime.now(timezone.utc)

    async def _create_slice_for_kernel(self, kernel: KernelRow) -> None:
        now = datetime.now(timezone.utc)
        slice_start = kernel.last_slice_end or kernel.started_at

        # Gap detection: Gap occurred if last slice is before server start
        gap_detected = (
            kernel.last_slice_end is not None and
            kernel.last_slice_end < self._server_started_at
        )

        if gap_detected:
            gap_hours = (now - slice_start).total_seconds() / 3600

            if self._config.gap_policy == SliceGapPolicy.IGNORE:
                # Ignore gap period: Start fresh from server start time
                slice_start = self._server_started_at
            elif gap_hours > self._config.max_gap_hours:
                # Gap exceeds max_gap_hours: Warn and interpolate only max_gap_hours
                log.warning(f"Large gap detected ({gap_hours:.1f}h), limiting to {self._config.max_gap_hours}h")
                slice_start = now - timedelta(hours=self._config.max_gap_hours)

        # Create slice (slice_start ~ now)
        ...
```

**Gap Handling Flow:**
```
On server start (server_started_at = 10:25):
├── Kernel K1's last_slice_end = 10:05 (last slice before server downtime)
│
├── [gap_policy = interpolate]
│   ├── gap_hours = 20 min (10:05 → 10:25)
│   └── gap_hours <= max_gap_hours → create 10:05-10:30 slice (interpolate)
│
└── [gap_policy = ignore]
    └── Start from server_started_at → create 10:25-10:30 slice
```

```python
# Based on batch execution time
slice_end = datetime.now(timezone.utc)  # Trigger time
slice_start = kernel.last_slice_end or kernel.started_at
# slice_end - slice_start is approximately 5 min (may not be exactly 5 min)
```

**Justification for Allowing Loss:**
- Fair Share is for determining relative priority
- Same loss for all users maintains relative fairness
- Loss can occur for various reasons such as infrastructure issues
- Loss detection logging is for debugging purposes only (no alerts needed)

**Configuration Example:**
```python
# resource_groups.scheduler_opts
{
    "gap_policy": "interpolate",  # or "ignore"
    "max_gap_hours": 24,          # Max gap period for interpolate (hours)
}
```

#### Slice vs Bucket Relationship

```
kernel_usage_records (5-minute slices)
├── 10:00-10:05 → ┐
├── 10:05-10:10 → │
├── 10:10-10:15 → │
├── 10:15-10:20 → ├── user_usage_buckets (decay_unit_days=1)
├── 10:20-10:25 → │     period_start: 2026-01-13
├── ...          → │     period_end: 2026-01-13
└── 23:55-00:00 → ┘     resource_usage: SUM(slices)
```

### 5. Fair Share Concept Definitions

#### Share vs Fair Share Factor

Two core concepts used in Fair Share scheduling:

| Concept | Name | Description | Configuration | Effect |
|------|------|------|-----------|------|
| **Share** | Allocation Weight | Resource allocation ratio assigned to user | Admin-configured | Higher share = higher priority at same usage |
| **Fair Share Factor** | Fairness Score | Current priority based on past usage | Auto-calculated | Higher factor = higher priority |

**Formula:**
```
Fair Share Factor = 2^(-Effective_Usage / Share)

- Share (S): Allocated ratio (product of weights)
- Effective Usage (UH): Cumulative usage with time decay applied
- Fair Share Factor (F): Final priority score (0 ~ 1)
```

**Example:**
```
User A: Share=2, used GPU 10 hours yesterday
User B: Share=1, used GPU 10 hours yesterday

After Decay (Effective Usage):
- User A: UH = 10 (hours)
- User B: UH = 10 (hours)

Fair Share Factor:
- User A: F = 2^(-10/2) = 2^(-5) ≈ 0.031
- User B: F = 2^(-10/1) = 2^(-10) ≈ 0.001

Result: User A gets priority (same usage but 2x Share)
```

**Terminology:**
- **Share/Weight**: "Allocated ratio" configured by admin
- **Fair Share Factor**: "Current priority" calculated by system
- **Effective Usage**: "Effective usage" with decay applied

#### Hierarchical Share Structure

Share (Weight) is applied in a Domain → Project → User hierarchical structure.

```
                    ┌─────────────────────┐
                    │   Resource Group     │
                    │   Total: 100%       │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Domain A   │     │  Domain B   │     │  Domain C   │
    │  weight: 2  │     │  weight: 1  │     │  weight: 1  │
    │  share: 50% │     │  share: 25% │     │  share: 25% │
    └──────┬──────┘     └──────┬──────┘     └─────────────┘
           │                   │
     ┌─────┴─────┐       ┌─────┴─────┐
     ▼           ▼       ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Project 1│ │Project 2│ │Project 3│ │Project 4│
│weight: 1│ │weight: 3│ │weight: 1│ │weight: 1│
│share:   │ │share:   │ │share:   │ │share:   │
│12.5%    │ │37.5%    │ │12.5%    │ │12.5%    │
└────┬────┘ └────┬────┘ └─────────┘ └─────────┘
     │           │
  ┌──┴──┐     ┌──┴──┐
  ▼     ▼     ▼     ▼
┌────┐┌────┐┌────┐┌────┐
│U1  ││U2  ││U3  ││U4  │
│w:1 ││w:1 ││w:2 ││w:1 │
└────┘└────┘└────┘└────┘
```

#### Effective Share Calculation

```
User's Effective Share = Domain_weight × Project_weight × User_weight
                        ─────────────────────────────────────────────
                              Σ(All Users' weight products)

Example:
- Domain A (weight=2), Project 2 (weight=3), User 3 (weight=2)
- Effective Share = (2 × 3 × 2) / Total = 12 / Total
```

### 6. FairShareSequencer Implementation

```python
class SliceGapPolicy(StrEnum):
    """Slice gap handling policy."""
    INTERPOLATE = "interpolate"  # Assume server was running and interpolate
    IGNORE = "ignore"            # Exclude unknown period from aggregation


@dataclass(frozen=True)
class FairShareConfig:
    """Fair Share scheduling configuration.

    Read from resource group's scheduler_opts.
    Only Flat decay method is supported (Slurm compatible, computationally efficient).
    """
    half_life_days: int = 7           # Half-life (days)
    lookback_days: int = 28           # Lookback period (days), recommend multiples of half-life
    decay_unit_days: int = 1          # Decay unit (days), recommend same as half_life_days for Flat method
    default_weight: Decimal = Decimal("1.0")  # Default weight (when tier not configured)
    gap_policy: SliceGapPolicy = SliceGapPolicy.INTERPOLATE  # Gap handling policy
    max_gap_hours: int = 24           # Max gap period for interpolate (hours)


@dataclass(frozen=True)
class HierarchyWeight:
    """Per-tier weight information.

    Weight is a relative ratio without normalization.
    Higher effective_weight results in higher Fair Share Factor at same usage.
    (= higher priority)
    """
    domain_weight: Decimal
    project_weight: Decimal
    user_weight: Decimal

    @property
    def effective_weight(self) -> Decimal:
        """Effective weight (product of tiers).

        Example:
        - Domain(w=2) × Project(w=3) × User(w=1) = 6
        - Domain(w=1) × Project(w=1) × User(w=1) = 1

        A user with weight=6 has 6x the share at same usage
        compared to a user with weight=1.
        """
        return self.domain_weight * self.project_weight * self.user_weight


class FairShareSequencer(WorkloadSequencer):
    """Hierarchical Historical Fair Share based workload sequencer.

    Sorts by querying pre-calculated fair_share_factor from fair_shares table.
    Fair Share Factor calculation is performed every 5 minutes by the batch
    aggregation service (UsageAggregationService).
    """

    def __init__(
        self,
        fair_share_repository: FairShareRepository,
    ) -> None:
        self._fair_share_repository = fair_share_repository

    @property
    @override
    def name(self) -> str:
        return "FairShareSequencer"

    @override
    def success_message(self) -> str:
        return "Sessions sequenced using hierarchical Fair Share algorithm"

    @override
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """Sort workloads by Fair Share Factor.

        Queries cached fair_share_factor from fair_shares table.
        Higher Fair Share Factor = higher priority (less usage = higher priority).
        """
        if not workloads:
            return []

        resource_group = workloads[0].resource_group

        # Collect (user_uuid, project_id) pairs from workloads
        user_project_pairs = {(w.user_uuid, w.project_id) for w in workloads}

        # Query cached fair_share_factor from user_fair_shares table
        fair_shares = self._fair_share_repository.get_user_fair_shares(
            user_project_pairs=user_project_pairs,
            resource_group=resource_group,
        )
        # Returns: Mapping[tuple[uuid.UUID, uuid.UUID], UserFairShareRow]

        # Sort by Fair Share Factor descending (higher = higher priority)
        # Default 1.0 for entries not in fair_shares (highest priority, new user)
        return sorted(
            workloads,
            key=lambda w: -fair_shares.get(
                (w.user_uuid, w.project_id),
                _DEFAULT_FAIR_SHARE,
            ).fair_share_factor
        )


# Default Fair Share for new users (highest priority)
@dataclass(frozen=True)
class _DefaultFairShare:
    fair_share_factor: Decimal = Decimal("1.0")

_DEFAULT_FAIR_SHARE = _DefaultFairShare()
```

### 7. Batch Aggregation Service

```python
@dataclass
class AggregationResult:
    """Aggregation result."""
    slices_created: int
    buckets_updated: int


class UsageAggregationService:
    """Batch service that records kernel usage as slices and aggregates to buckets."""

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config: FairShareConfig,
        slice_interval_seconds: int = 300,  # 5 minutes
    ) -> None:
        self._db = db
        self._config = config
        self._slice_interval = slice_interval_seconds

    async def aggregate(self) -> AggregationResult:
        """Execute batch aggregation (5-minute cycle).

        1. Create new slices for running kernels (kernel_usage_records)
        2. Aggregate slices → buckets (*_usage_buckets)
        3. Calculate and update Fair Share Factor (*_fair_shares)
        """
        async with self._db.begin_session() as db_sess:
            # 1. Create new slices for running kernels
            slices_created = await self._create_slices_for_running_kernels(db_sess)

            # 2. Aggregate slices → buckets (Mutable + period_end extension)
            buckets_updated = await self._aggregate_slices_to_buckets(db_sess)

            # 3. Calculate Fair Share Factor and update *_fair_shares tables
            await self._update_fair_shares(db_sess)

            return AggregationResult(
                slices_created=slices_created,
                buckets_updated=buckets_updated,
            )

    async def _create_slices_for_running_kernels(self, db_sess: SASession) -> int:
        """Create new period slices for running kernels."""
        now = datetime.now(timezone.utc)

        # Query running kernels
        stmt = (
            sa.select(KernelRow)
            .where(KernelRow.status.in_(RUNNING_STATUSES))
        )
        result = await db_sess.execute(stmt)
        running_kernels = result.scalars().all()

        slices_created = 0
        for kernel in running_kernels:
            # Determine last slice end time
            period_start = kernel.last_slice_end or kernel.started_at
            period_end = now

            duration_seconds = (period_end - period_start).total_seconds()
            if duration_seconds <= 0:
                continue

            # Calculate resource usage
            resource_usage = self._calculate_usage(
                kernel.occupied_slots, duration_seconds
            )

            # Create new slice record
            slice_record = KernelUsageRecordRow(
                kernel_id=kernel.id,
                session_id=kernel.session_id,
                user_uuid=kernel.user_uuid,
                group_id=kernel.group_id,
                domain_name=kernel.domain_name,
                resource_group=kernel.resource_group,
                period_start=period_start,
                period_end=period_end,
                resource_usage=resource_usage,
            )
            db_sess.add(slice_record)

            # Update kernel's last_slice_end
            kernel.last_slice_end = period_end
            slices_created += 1

        return slices_created

    async def _aggregate_slices_to_buckets(self, db_sess: SASession) -> int:
        """Aggregate slices to buckets (Mutable + period_end extension strategy).

        Bucket update strategy:
        1. Query current active bucket (most recent period_start)
        2. If new slice date is within decay_unit, extend existing bucket (UPDATE period_end)
        3. If exceeds decay_unit, create new bucket (INSERT)

        Invariant: period_end - period_start < decay_unit_days
        """
        today = date.today()
        buckets_updated = 0

        # Query slices not yet reflected in buckets
        # (aggregate per user from kernel_usage_records)
        for user_uuid, project_id, domain_name, resource_group in user_project_combinations:
            # Query user's current active bucket
            current_bucket = await self._get_latest_bucket(
                db_sess, user_uuid, project_id, resource_group
            )

            # Sum new slices' usage
            new_usage = await self._sum_new_slices(
                db_sess, user_uuid, project_id, resource_group
            )

            if current_bucket is None:
                # Create first bucket
                await self._insert_bucket(
                    db_sess, user_uuid, project_id, domain_name, resource_group,
                    period_start=today, period_end=today,
                    resource_usage=new_usage,
                )
            elif (today - current_bucket.period_start).days < self._config.decay_unit_days:
                # Within decay_unit → extend existing bucket
                current_bucket.period_end = today
                current_bucket.resource_usage += new_usage
            else:
                # Exceeds decay_unit → create new bucket
                await self._insert_bucket(
                    db_sess, user_uuid, project_id, domain_name, resource_group,
                    period_start=today, period_end=today,
                    resource_usage=new_usage,
                )

            buckets_updated += 1

        return buckets_updated

    async def _update_fair_shares(self, db_sess: SASession) -> int:
        """Update fair_shares table based on buckets.

        For each (user, project, resource_group) combination:
        1. Query buckets within lookback_days range
        2. Calculate total_decayed_usage with decay applied
        3. Calculate Fair Share Factor: F = 2^(-UH/S)
        4. UPSERT to user_fair_shares table
        """
        # ... fair share factor calculation and save logic
        pass

    async def recalculate_buckets(self) -> int:
        """Recalculate all buckets when decay configuration changes."""
        async with self._db.begin_session() as db_sess:
            # Delete existing buckets
            await db_sess.execute(sa.delete(UserUsageBucketRow))
            await db_sess.execute(sa.delete(ProjectUsageBucketRow))
            await db_sess.execute(sa.delete(DomainUsageBucketRow))

            # Re-aggregate from raw slices
            return await self._aggregate_slices_to_buckets(db_sess)
```

### 8. Sequencer Registration

```python
# src/ai/backend/manager/sokovan/scheduler/provisioner/provisioner.py

from .sequencers import (
    DRFSequencer,
    FairShareSequencer,
    FIFOSequencer,
    LIFOSequencer,
    WorkloadSequencer,
)

@classmethod
def _make_sequencer_pool(
    cls,
    fair_share_repository: FairShareRepository,
) -> Mapping[str, WorkloadSequencer]:
    """Initialize sequencer pool."""
    pool: dict[str, WorkloadSequencer] = defaultdict(DRFSequencer)
    pool["fifo"] = FIFOSequencer()
    pool["lifo"] = LIFOSequencer()
    pool["drf"] = DRFSequencer()
    pool["fairshare"] = FairShareSequencer(
        fair_share_repository=fair_share_repository,
    )
    return pool
```

### 9. Per-tier Share (Weight) Storage Structure

#### Design Principles

Share (Weight) is **managed per Resource Group**:
- Weight may or may not be needed depending on scheduler type
- Only meaningful in resource groups using Fair Share scheduler
- Not added directly to Domain/Group/User tables (entities independent of scheduler)

#### Fair Shares Tables (Per-tier State Summary)

Separate from Usage Buckets, tables storing the **current Fair Share state** for each entity.
Stores weight (configured value) and calculated values (decayed_usage, factor) together for user visibility.

**Table Structure Overview:**
```
Usage Buckets (period-based, multiple rows)     Fair Shares (state summary, 1 row per entity)
─────────────────────────────────────────────   ─────────────────────────────────────────────
domain_usage_buckets                            domain_fair_shares
project_usage_buckets        ──────→            project_fair_shares
user_usage_buckets           aggregation        user_fair_shares

period_start, period_end                        weight (configured value)
resource_usage (for that period)                total_decayed_usage (summed value)
capacity_snapshot (for normalization)           normalized_usage (weighted avg of usage/capacity)
                                                fair_share_factor (calculated value)
                                                resource_weights (from scheduler_opts)
                                                lookback_start/end (calculation period)
                                                half_life_days, decay_unit_days (calculation params)
```

##### domain_fair_shares Table

```python
class DomainFairShareRow(Base):
    """Per-domain Fair Share state.

    Stores weight (configured value) and calculated values together for current state.
    """

    __tablename__ = "domain_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )

    # Configured value (admin-set)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=False,
        default=Decimal("1.0"),
    )

    # Calculated values (updated by batch)
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Time decay applied total usage (resource-seconds)"
    )
    normalized_usage: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
                "IMPORTANT: Both usage and capacity must be in resource-seconds. "
                "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])"
    )
    fair_share_factor: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
                "Higher value = less past usage = higher scheduling priority. "
                "Formula: F = 2^(-normalized_usage / weight)"
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Timestamp when fair_share_factor was last recalculated by batch job."
    )

    # Calculation parameters (tracks conditions used for calculation)
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource weights used in fair share calculation. "
                "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}"
    )
    lookback_start: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup start date used in calculation"
    )
    lookback_end: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup end date used in calculation"
    )
    half_life_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7,
        comment="Half-life used in calculation (days)"
    )
    lookback_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=28,
        comment="Lookback period used in calculation (days)"
    )
    decay_unit_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Aggregation unit used in calculation (days)"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    __table_args__ = (
        UniqueConstraint("resource_group", "domain_name", name="uq_domain_fair_share"),
        Index("ix_domain_fair_share_lookup", "resource_group", "domain_name"),
    )
```

##### project_fair_shares Table

```python
class ProjectFairShareRow(Base):
    """Per-project Fair Share state."""

    __tablename__ = "project_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )

    # Configured value (admin-set)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=False,
        default=Decimal("1.0"),
    )

    # Calculated values (updated by batch)
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
    )
    normalized_usage: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
                "IMPORTANT: Both usage and capacity must be in resource-seconds. "
                "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])"
    )
    fair_share_factor: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
                "Higher value = less past usage = higher scheduling priority. "
                "Formula: F = 2^(-normalized_usage / weight)"
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Timestamp when fair_share_factor was last recalculated by batch job."
    )

    # Calculation parameters (tracks conditions used for calculation)
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource weights used in fair share calculation. "
                "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}"
    )
    lookback_start: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup start date used in calculation"
    )
    lookback_end: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup end date used in calculation"
    )
    half_life_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7,
        comment="Half-life used in calculation (days)"
    )
    lookback_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=28,
        comment="Lookback period used in calculation (days)"
    )
    decay_unit_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Aggregation unit used in calculation (days)"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    project: Mapped[GroupRow | None] = relationship("GroupRow")
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    __table_args__ = (
        UniqueConstraint("resource_group", "project_id", name="uq_project_fair_share"),
        Index("ix_project_fair_share_lookup", "resource_group", "project_id"),
    )
```

##### user_fair_shares Table

```python
class UserFairShareRow(Base):
    """Per-user Fair Share state.

    Since a User can belong to multiple Projects, distinguished by (user_uuid, project_id) combination.
    """

    __tablename__ = "user_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    resource_group: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )

    # Configured value (admin-set)
    weight: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=False,
        default=Decimal("1.0"),
    )

    # Calculated values (updated by batch)
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
    )
    normalized_usage: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
                "IMPORTANT: Both usage and capacity must be in resource-seconds. "
                "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])"
    )
    fair_share_factor: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
                "Higher value = less past usage = higher scheduling priority. "
                "Formula: F = 2^(-normalized_usage / weight)"
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Timestamp when fair_share_factor was last recalculated by batch job."
    )

    # Calculation parameters (tracks conditions used for calculation)
    # - Used to determine if recalculation is needed when config changes
    # - Provides visibility of calculation conditions to users
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        ResourceSlotColumn(), nullable=False, default=ResourceSlot(),
        comment="Resource weights used in fair share calculation. "
                "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}"
    )
    lookback_start: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup start date used in calculation"
    )
    lookback_end: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
        comment="Lookup end date used in calculation"
    )
    half_life_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7,
        comment="Half-life used in calculation (days)"
    )
    lookback_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=28,
        comment="Lookback period used in calculation (days)"
    )
    decay_unit_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Aggregation unit used in calculation (days)"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped[UserRow | None] = relationship("UserRow")
    project: Mapped[GroupRow | None] = relationship("GroupRow")
    domain: Mapped[DomainRow | None] = relationship("DomainRow")

    __table_args__ = (
        UniqueConstraint(
            "resource_group", "user_uuid", "project_id",
            name="uq_user_fair_share"
        ),
        Index("ix_user_fair_share_lookup", "resource_group", "user_uuid", "project_id"),
    )
```

**Usage Examples:**
```python
# GPU cluster with research domain (2x weight configured)
DomainFairShareRow(
    resource_group="gpu-cluster",
    domain_name="research",
    weight=Decimal("2.0"),
    # Below are calculated/updated by batch
    total_decayed_usage=ResourceSlot({"cpu": 50000, "mem": 100000, "cuda.device": 3600}),
    normalized_usage=Decimal("0.15"),  # Weighted average of (usage/capacity)
    fair_share_factor=Decimal("0.94574160838"),  # 2^(-0.15/2.0)
    resource_weights=ResourceSlot({"cpu": 1.0, "mem": 1.0, "cuda.device": 10.0}),
    last_calculated_at=datetime.now(timezone.utc),
)

# GPU cluster with ml-team project
ProjectFairShareRow(
    resource_group="gpu-cluster",
    project_id=ml_team_id,
    domain_name="research",
    weight=Decimal("1.5"),
    total_decayed_usage=ResourceSlot({"cpu": 30000, "cuda.device": 5000}),
    normalized_usage=Decimal("0.25"),
    fair_share_factor=Decimal("0.89089871814"),  # 2^(-0.25/1.5)
    resource_weights=ResourceSlot({"cpu": 1.0, "mem": 1.0, "cuda.device": 10.0}),
    last_calculated_at=datetime.now(timezone.utc),
)

# GPU cluster with specific user
UserFairShareRow(
    resource_group="gpu-cluster",
    user_uuid=user_uuid,
    project_id=ml_team_id,
    domain_name="research",
    weight=Decimal("1.0"),
    total_decayed_usage=ResourceSlot({"cpu": 10000, "cuda.device": 2000}),
    normalized_usage=Decimal("0.10"),
    fair_share_factor=Decimal("0.93303299153"),  # 2^(-0.10/1.0)
    resource_weights=ResourceSlot({"cpu": 1.0, "mem": 1.0, "cuda.device": 10.0}),
    last_calculated_at=datetime.now(timezone.utc),
)
```

#### FairShareRepository Implementation

```python
class FairShareDBSource:
    """Fair Share related DB data source."""

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_user_fair_shares(
        self,
        db_sess: SASession,
        user_project_pairs: set[tuple[uuid.UUID, uuid.UUID]],
        resource_group: str,
    ) -> Mapping[tuple[uuid.UUID, uuid.UUID], UserFairShareRow]:
        """Query users' Fair Share info (per user_uuid, project_id).

        user_project_pairs: {(user_uuid, project_id), ...} combination set
        """
        if not user_project_pairs:
            return {}

        # Match exactly by (user_uuid, project_id) combination
        conditions = [
            sa.and_(
                UserFairShareRow.user_uuid == user_uuid,
                UserFairShareRow.project_id == project_id,
            )
            for user_uuid, project_id in user_project_pairs
        ]
        stmt = (
            sa.select(UserFairShareRow)
            .where(
                UserFairShareRow.resource_group == resource_group,
                sa.or_(*conditions),
            )
        )
        result = await db_sess.execute(stmt)
        rows = result.scalars().all()
        return {(r.user_uuid, r.project_id): r for r in rows}

    async def get_hierarchy_fair_shares(
        self,
        db_sess: SASession,
        domain_names: set[str],
        project_ids: set[uuid.UUID],
        resource_group: str,
    ) -> tuple[
        Mapping[str, DomainFairShareRow],
        Mapping[uuid.UUID, ProjectFairShareRow],
    ]:
        """Query domain/project Fair Share info."""
        # Domain Fair Shares
        domain_stmt = (
            sa.select(DomainFairShareRow)
            .where(
                DomainFairShareRow.resource_group == resource_group,
                DomainFairShareRow.domain_name.in_(domain_names),
            )
        )
        domain_result = await db_sess.execute(domain_stmt)
        domain_shares = {r.domain_name: r for r in domain_result.scalars().all()}

        # Project Fair Shares
        project_stmt = (
            sa.select(ProjectFairShareRow)
            .where(
                ProjectFairShareRow.resource_group == resource_group,
                ProjectFairShareRow.project_id.in_(project_ids),
            )
        )
        project_result = await db_sess.execute(project_stmt)
        project_shares = {r.project_id: r for r in project_result.scalars().all()}

        return domain_shares, project_shares

    async def upsert_user_fair_share(
        self,
        db_sess: SASession,
        resource_group: str,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        weight: Decimal | None = None,
        total_decayed_usage: ResourceSlot | None = None,
        fair_share_factor: Decimal | None = None,
    ) -> UserFairShareRow:
        """Upsert user Fair Share info (weight config or calculated value update)."""
        stmt = (
            sa.select(UserFairShareRow)
            .where(
                UserFairShareRow.resource_group == resource_group,
                UserFairShareRow.user_uuid == user_uuid,
                UserFairShareRow.project_id == project_id,
            )
        )
        result = await db_sess.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            row = UserFairShareRow(
                resource_group=resource_group,
                user_uuid=user_uuid,
                project_id=project_id,
                domain_name=domain_name,
            )
            db_sess.add(row)

        # Update configured or calculated values
        if weight is not None:
            row.weight = weight
        if total_decayed_usage is not None:
            row.total_decayed_usage = total_decayed_usage
        if fair_share_factor is not None:
            row.fair_share_factor = fair_share_factor
            row.last_calculated_at = datetime.now(timezone.utc)

        return row

    async def get_fair_share_config(
        self, db_sess: SASession, resource_group: str
    ) -> FairShareConfig:
        """Query resource group's Fair Share configuration."""
        stmt = sa.select(ScalingGroupRow).where(
            ScalingGroupRow.name == resource_group
        )
        result = await db_sess.execute(stmt)
        sg_row = result.scalar_one_or_none()

        if sg_row and sg_row.scheduler_opts:
            opts = sg_row.scheduler_opts
            return FairShareConfig(
                half_life_days=opts.get("half_life_days", 7),
                lookback_days=opts.get("lookback_days", 28),
                decay_unit_days=opts.get("decay_unit_days", 1),
                default_weight=Decimal(str(opts.get("default_weight", "1.0"))),
                gap_policy=SliceGapPolicy(opts.get("gap_policy", "interpolate")),
                max_gap_hours=opts.get("max_gap_hours", 24),
            )

        return FairShareConfig()  # Return default values


class FairShareRepository:
    """Fair Share related data Repository."""

    def __init__(self, db_source: FairShareDBSource) -> None:
        self._db_source = db_source

    async def get_user_fair_shares(
        self,
        user_project_pairs: set[tuple[uuid.UUID, uuid.UUID]],
        resource_group: str,
    ) -> Mapping[tuple[uuid.UUID, uuid.UUID], UserFairShareRow]:
        """Query users' Fair Share info (per user_uuid, project_id)."""
        async with self._db_source._db.begin_readonly_session() as db_sess:
            return await self._db_source.get_user_fair_shares(
                db_sess, user_project_pairs, resource_group
            )

    async def get_fair_share_config(
        self, resource_group: str
    ) -> FairShareConfig:
        """Query resource group's Fair Share configuration."""
        async with self._db_source._db.begin_readonly_session() as db_sess:
            return await self._db_source.get_fair_share_config(db_sess, resource_group)
```

## Configuration

### Configuration Parameters (Per Resource Group)

Stored in the `resource_groups.scheduler_opts` JSONB column.

| Parameter | Type | Default | Description |
|---------|------|--------|------|
| `half_life_days` | int | 7 | Usage half-life (days). 7-day-old usage has 50% weight |
| `lookback_days` | int | 28 | Lookback period (days). Recommend multiples of half-life |
| `decay_unit_days` | int | 1 | Bucket aggregation unit (days) |
| `slice_interval_seconds` | int | 300 | Slice creation cycle (seconds) |
| `default_weight` | Decimal | 1.0 | Default weight (when tier not configured) |
| `gap_policy` | SliceGapPolicy | "interpolate" | Slice gap handling policy: "interpolate" or "ignore" |
| `max_gap_hours` | int | 24 | Max gap period for interpolate (hours) |

### Per-tier Weight Configuration

Managed per Resource Group in `domain_fair_shares`, `project_fair_shares`, `user_fair_shares` tables.

```python
# GPU cluster with research domain at 2x weight
DomainFairShareRow(
    resource_group="gpu-cluster",
    domain_name="research",
    weight=Decimal("2.0"),
    # total_decayed_usage, fair_share_factor calculated by batch
)

# GPU cluster with ml-team project at 1.5x weight
ProjectFairShareRow(
    resource_group="gpu-cluster",
    project_id=ml_team_id,
    domain_name="research",
    weight=Decimal("1.5"),
)

# GPU cluster with specific user at 1.0 weight (default)
UserFairShareRow(
    resource_group="gpu-cluster",
    user_uuid=user_uuid,
    project_id=ml_team_id,
    domain_name="research",
    weight=Decimal("1.0"),
)

# Effective weight calculation (relative ratio without normalization)
# User's effective_weight = domain × project × user = 2.0 × 1.5 × 1.0 = 3.0
```

### Resource Group Configuration Example

```python
# Scheduler and options specified in Resource Group configuration
resource_group = {
    "name": "gpu-cluster",
    "scheduler": "fairshare",  # "fifo" | "lifo" | "drf" | "fairshare"
    "scheduler_opts": {
        "half_life_days": 7,
        "lookback_days": 28,
        "decay_unit_days": 7,
        "default_weight": "1.0",
        "gap_policy": "interpolate",
        "max_gap_hours": 24,
    }
}
```

### Behavior When Decay Configuration Changes

When `decay_unit_days` or `half_life_days` changes:
1. Invalidate `user_usage_buckets` cache (per resource group)
2. Regenerate buckets from `kernel_usage_records` raw data
3. No scheduling pause required (can query raw directly during cache regeneration)

### Scheduler Type-based Configuration Parsing (Enum-based Union)

Parse the `scheduler_opts` JSONB field into different types based on scheduler type.

#### Scheduler Type Definition

```python
class SchedulerType(StrEnum):
    """Scheduler types."""
    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIRSHARE = "fairshare"
```

#### Per-scheduler Configuration Types

```python
from pydantic import BaseModel, ConfigDict


class FIFOConfig(BaseModel):
    """FIFO scheduler configuration (no options)."""
    model_config = ConfigDict(frozen=True)


class LIFOConfig(BaseModel):
    """LIFO scheduler configuration (no options)."""
    model_config = ConfigDict(frozen=True)


class DRFConfig(BaseModel):
    """DRF scheduler configuration (no options)."""
    model_config = ConfigDict(frozen=True)


class FairShareConfig(BaseModel):
    """Fair Share scheduler configuration."""
    model_config = ConfigDict(frozen=True)

    half_life_days: int = 7
    lookback_days: int = 28
    decay_unit_days: int = 1
    default_weight: Decimal = Decimal("1.0")
    gap_policy: SliceGapPolicy = SliceGapPolicy.INTERPOLATE
    max_gap_hours: int = 24


# Union type
SchedulerConfig = FIFOConfig | LIFOConfig | DRFConfig | FairShareConfig

# Scheduler type → configuration class mapping
SCHEDULER_CONFIG_MAP: dict[SchedulerType, type[SchedulerConfig]] = {
    SchedulerType.FIFO: FIFOConfig,
    SchedulerType.LIFO: LIFOConfig,
    SchedulerType.DRF: DRFConfig,
    SchedulerType.FAIRSHARE: FairShareConfig,
}
```

#### Configuration Parsing Function

```python
def parse_scheduler_config(
    scheduler: str,
    scheduler_opts: dict[str, Any] | None,
) -> SchedulerConfig:
    """Parse into appropriate configuration type based on scheduler type.

    Args:
        scheduler: Scheduler type string ("fifo", "drf", "fairshare", etc.)
        scheduler_opts: resource_groups.scheduler_opts JSONB value

    Returns:
        Type-appropriate configuration object
    """
    scheduler_type = SchedulerType(scheduler)
    config_cls = SCHEDULER_CONFIG_MAP[scheduler_type]
    return config_cls.model_validate(scheduler_opts or {})
```

#### Usage Examples

```python
# Query configuration in Repository
class ScalingGroupRepository:
    async def get_scheduler_config(
        self, resource_group: str
    ) -> SchedulerConfig:
        """Query resource group's scheduler configuration."""
        async with self._db.begin_readonly_session() as db_sess:
            stmt = sa.select(ScalingGroupRow).where(
                ScalingGroupRow.name == resource_group
            )
            result = await db_sess.execute(stmt)
            sg_row = result.scalar_one_or_none()

            if not sg_row:
                raise ScalingGroupNotFound(resource_group)

            return parse_scheduler_config(
                scheduler=sg_row.scheduler,
                scheduler_opts=sg_row.scheduler_opts,
            )


# Type-safe usage in Sequencer
class FairShareSequencer(WorkloadSequencer):
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        config = self._repository.get_scheduler_config(resource_group)

        # Type check ensures FairShareConfig
        if not isinstance(config, FairShareConfig):
            raise InvalidSchedulerType(
                f"FairShareSequencer requires FairShareConfig, got {type(config)}"
            )

        # After this, config is inferred as FairShareConfig type
        half_life = config.half_life_days  # Type safe
        ...
```

#### Benefits

1. **Type Safety**: Per-scheduler configurations are clearly typed
2. **JSONB Preserved**: Uses existing `scheduler_opts` column without schema changes
3. **Easy Extension**: Just add types for new schedulers
4. **IDE Support**: Auto-completion, type error detection available

## API Design

### REST API

#### Resource Group Fair Share Configuration Read/Update

```http
# Read
GET /resource-groups/{resource_group}/scheduler-options
Response: {
    "scheduler": "fairshare",
    "scheduler_opts": {
        "half_life_days": 7,
        "lookback_days": 28,
        "decay_unit_days": 7,
        "default_weight": "1.0",
        "gap_policy": "interpolate",
        "max_gap_hours": 24
    }
}

# Update
PATCH /resource-groups/{resource_group}/scheduler-options
Body: {
    "scheduler": "fairshare",
    "scheduler_opts": {
        "half_life_days": 14
    }
}
```

#### Fair Share Weight Management

```http
# List weights
GET /resource-groups/{resource_group}/fair-share-weights
Response: {
    "items": [
        {"id": "...", "target_type": "domain", "target_id": "research", "weight": "2.0"},
        {"id": "...", "target_type": "project", "target_id": "<uuid>", "weight": "1.5"},
        {"id": "...", "target_type": "user", "target_id": "<uuid>", "weight": "1.0"}
    ]
}

# Bulk Upsert weights (weight=null means delete)
PUT /resource-groups/{resource_group}/fair-share-weights
Body: {
    "items": [
        {"target_type": "domain", "target_id": "research", "weight": "2.0"},   # upsert
        {"target_type": "project", "target_id": "<uuid>", "weight": "1.5"},    # upsert
        {"target_type": "user", "target_id": "<uuid>", "weight": null}         # delete
    ]
}
Response: {
    "ok": true,
    "upserted": 2,
    "deleted": 1
}
```

#### User Fair Share Factor Query (Read-only)

```http
# Query specific user's current Fair Share Factor
GET /resource-groups/{resource_group}/fair-share-status?user_uuid={user_uuid}
Response: {
    "user_uuid": "...",
    "effective_usage": "1234.56",
    "effective_weight": "3.0",
    "fair_share_factor": "0.125"
}

# All users' Fair Share ranking within Resource Group
GET /resource-groups/{resource_group}/fair-share-status
Response: {
    "items": [
        {"user_uuid": "...", "fair_share_factor": "1.0", "rank": 1},
        {"user_uuid": "...", "fair_share_factor": "0.5", "rank": 2},
        ...
    ]
}
```

### GraphQL API

#### Type Definitions

```graphql
# Enums
enum FairShareWeightTargetType {
    DOMAIN
    PROJECT
    USER
}

enum SliceGapPolicy {
    INTERPOLATE
    IGNORE
}
```

##### Fair Share Weight (Admin Configuration)

Weight policy data configured by admin (stored in DB).

```graphql
type FairShareWeightNode implements Node {
    id: ID!
    resource_group: String!
    target_type: FairShareWeightTargetType!
    target_id: String!
    weight: String!  # Configured weight (default 1.0 if not set)
}

type FairShareWeightConnection {
    edges: [FairShareWeightEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type FairShareWeightEdge {
    node: FairShareWeightNode!
    cursor: String!
}
```

##### Fair Share (Per-tier State)

Priority information periodically calculated by batch (updated every 5 minutes, stored in `*_fair_shares` tables).
Includes weight, effective_usage, fair_share_factor, and rank per tier.

```graphql
# Domain Fair Share
# - Domain-level Fair Share information
# - effective_usage: Sum of all users' usage in the domain
type DomainFairShare {
    domain_name: String!
    weight: String!               # Domain weight (admin-configured)
    effective_usage: String!      # Domain total usage (decay applied)
    fair_share_factor: String!    # Domain-based Factor
    rank: Int                     # Domain rank
    last_calculated_at: DateTime  # Last calculation time
    # Calculation parameters (tracks conditions used for calculation)
    lookback_start: Date          # Lookup start date
    lookback_end: Date            # Lookup end date
    half_life_days: Int           # Decay half-life
    lookback_days: Int            # History lookup period
    decay_unit_days: Int          # Decay calculation unit
    # Sub-tier access
    project_fair_shares: ProjectFairShareConnection!
}

type DomainFairShareConnection {
    edges: [DomainFairShareEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type DomainFairShareEdge {
    node: DomainFairShare!
    cursor: String!
}

# Project Fair Share
# - Project-level Fair Share information
# - effective_usage: Sum of all users' usage in the project
type ProjectFairShare {
    project_id: UUID!
    domain_name: String!
    weight: String!               # Project weight (admin-configured)
    effective_usage: String!      # Project total usage (decay applied)
    fair_share_factor: String!    # Project-based Factor
    rank: Int                     # Project rank (within Domain)
    last_calculated_at: DateTime  # Last calculation time
    # Calculation parameters (tracks conditions used for calculation)
    lookback_start: Date          # Lookup start date
    lookback_end: Date            # Lookup end date
    half_life_days: Int           # Decay half-life
    lookback_days: Int            # History lookup period
    decay_unit_days: Int          # Decay calculation unit
    # Sub-tier access
    user_fair_shares: UserFairShareConnection!
}

type ProjectFairShareConnection {
    edges: [ProjectFairShareEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type ProjectFairShareEdge {
    node: ProjectFairShare!
    cursor: String!
}

# User Fair Share
# - User-level Fair Share information
# - share: Product of Domain × Project × User weights
# - effective_usage: User's usage (within specific project)
type UserFairShare {
    user_uuid: UUID!
    project_id: UUID!
    domain_name: String!
    share: String!                # Domain × Project × User weight product
    effective_usage: String!      # User usage (decay applied)
    fair_share_factor: String!    # Final priority (0~1, higher = higher priority)
    rank: Int                     # User rank (overall or within Project)
    last_calculated_at: DateTime  # Last calculation time
    # Calculation parameters (tracks conditions used for calculation)
    lookback_start: Date          # Lookup start date
    lookback_end: Date            # Lookup end date
    half_life_days: Int           # Decay half-life
    lookback_days: Int            # History lookup period
    decay_unit_days: Int          # Decay calculation unit
}

type UserFairShareConnection {
    edges: [UserFairShareEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type UserFairShareEdge {
    node: UserFairShare!
    cursor: String!
}
```

##### Usage Bucket (Per-tier History)

Period-based usage history (aggregated data stored in DB).

```graphql
# Domain Usage Bucket
type DomainUsageBucketNode implements Node {
    id: ID!
    domain_name: String!
    resource_group: String!
    period_start: Date!
    period_end: Date!
    decay_unit_days: Int!
    resource_usage: JSONString!
    created_at: DateTime!
    updated_at: DateTime!
}

type DomainUsageBucketConnection {
    edges: [DomainUsageBucketEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type DomainUsageBucketEdge {
    node: DomainUsageBucketNode!
    cursor: String!
}

# Project Usage Bucket
type ProjectUsageBucketNode implements Node {
    id: ID!
    project_id: UUID!
    domain_name: String!
    resource_group: String!
    period_start: Date!
    period_end: Date!
    decay_unit_days: Int!
    resource_usage: JSONString!
    created_at: DateTime!
    updated_at: DateTime!
}

type ProjectUsageBucketConnection {
    edges: [ProjectUsageBucketEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type ProjectUsageBucketEdge {
    node: ProjectUsageBucketNode!
    cursor: String!
}

# User Usage Bucket
type UserUsageBucketNode implements Node {
    id: ID!
    user_uuid: UUID!
    project_id: UUID!
    domain_name: String!
    resource_group: String!
    period_start: Date!
    period_end: Date!
    decay_unit_days: Int!
    resource_usage: JSONString!
    created_at: DateTime!
    updated_at: DateTime!
}

type UserUsageBucketConnection {
    edges: [UserUsageBucketEdge!]!
    pageInfo: PageInfo!
    count: Int!
}

type UserUsageBucketEdge {
    node: UserUsageBucketNode!
    cursor: String!
}
```

#### Filter Types

```graphql
# Fair Share Weight Filter
input FairShareWeightFilter {
    target_type: [FairShareWeightTargetType!]
    target_id: StringFilter
    AND: [FairShareWeightFilter!]
    OR: [FairShareWeightFilter!]
    NOT: [FairShareWeightFilter!]
}

# Domain Fair Share Filter
input DomainFairShareFilter {
    domain_name: StringFilter
    AND: [DomainFairShareFilter!]
    OR: [DomainFairShareFilter!]
    NOT: [DomainFairShareFilter!]
}

# Project Fair Share Filter
input ProjectFairShareFilter {
    project_id: UUIDFilter
    domain_name: StringFilter
    AND: [ProjectFairShareFilter!]
    OR: [ProjectFairShareFilter!]
    NOT: [ProjectFairShareFilter!]
}

# User Fair Share Filter
input UserFairShareFilter {
    user_uuid: UUIDFilter
    project_id: UUIDFilter
    domain_name: StringFilter
    AND: [UserFairShareFilter!]
    OR: [UserFairShareFilter!]
    NOT: [UserFairShareFilter!]
}

# Domain Usage Bucket Filter
input DomainUsageBucketFilter {
    domain_name: StringFilter
    period_start: DateFilter
    period_end: DateFilter
    AND: [DomainUsageBucketFilter!]
    OR: [DomainUsageBucketFilter!]
    NOT: [DomainUsageBucketFilter!]
}

# Project Usage Bucket Filter
input ProjectUsageBucketFilter {
    project_id: UUIDFilter
    domain_name: StringFilter
    period_start: DateFilter
    period_end: DateFilter
    AND: [ProjectUsageBucketFilter!]
    OR: [ProjectUsageBucketFilter!]
    NOT: [ProjectUsageBucketFilter!]
}

# User Usage Bucket Filter
input UserUsageBucketFilter {
    user_uuid: UUIDFilter
    project_id: UUIDFilter
    domain_name: StringFilter
    period_start: DateFilter
    period_end: DateFilter
    AND: [UserUsageBucketFilter!]
    OR: [UserUsageBucketFilter!]
    NOT: [UserUsageBucketFilter!]
}
```

#### Order Types

```graphql
# Fair Share Weight Order Fields
enum FairShareWeightOrderField {
    TARGET_TYPE
    TARGET_ID
    WEIGHT
}

# Fair Share Weight Order (inherits GQLOrderBy)
input FairShareWeightOrderBy {
    field: FairShareWeightOrderField!
    direction: OrderDirection = ASC
}

# User Fair Share Order Fields
enum UserFairShareOrderField {
    FAIR_SHARE_FACTOR
    EFFECTIVE_USAGE
    EFFECTIVE_WEIGHT
    RANK
}

# User Fair Share Order
input UserFairShareOrderBy {
    field: UserFairShareOrderField!
    direction: OrderDirection = DESC
}

# User Usage Bucket Order Fields
enum UserUsageBucketOrderField {
    PERIOD_START
    PERIOD_END
    CREATED_AT
    UPDATED_AT
}

# User Usage Bucket Order
input UserUsageBucketOrderBy {
    field: UserUsageBucketOrderField!
    direction: OrderDirection = DESC
}
```

#### Input Types

```graphql
# Weight Upsert Input (weight=null means delete)
input FairShareWeightInput {
    target_type: FairShareWeightTargetType!
    target_id: String!
    weight: String  # null means delete (apply default_weight 1.0)
}

# Per-tier Weight Bulk Configuration Input (alternative: structured form)
input FairShareWeightsBulkInput {
    domain_weights: [DomainWeightInput!]
    project_weights: [ProjectWeightInput!]
    user_weights: [UserWeightInput!]
}

input DomainWeightInput {
    domain_name: String!
    weight: String  # null means delete
}

input ProjectWeightInput {
    project_id: UUID!
    weight: String  # null means delete
}

input UserWeightInput {
    user_uuid: UUID!
    project_id: UUID!  # User can belong to multiple Projects
    weight: String  # null means delete
}

# Upsert Result (failures handled as GraphQL errors)
type UpsertFairShareWeightsResult {
    upserted_count: Int!                      # Number of created/modified items
    deleted_count: Int!                       # Number of deleted items (weight=null)
    affected_weights: [FairShareWeightNode!]! # Only items changed in this request
}
```

#### Query

```graphql
type Query {
    # Resource Group query (config only)
    resource_group(name: String!): ScalingGroup

    # ─────────────────────────────────────────────────────────────────
    # Fair Share Status Query (weight + calculated values combined)
    # - Per-tier weight, total_decayed_usage, fair_share_factor included
    # - weight is admin-configured, rest auto-updated by batch
    # ─────────────────────────────────────────────────────────────────

    # Domain-level Fair Share list
    domain_fair_shares(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: DomainFairShareFilter
        order: DomainFairShareOrderBy
    ): DomainFairShareConnection!

    # Specific Domain's Fair Share detail (includes sub-Projects)
    domain_fair_share(
        resource_group: String!
        domain_name: String!
    ): DomainFairShare

    # Project-level Fair Share list
    project_fair_shares(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: ProjectFairShareFilter
        order: ProjectFairShareOrderBy
    ): ProjectFairShareConnection!

    # Specific Project's Fair Share detail (includes sub-Users)
    project_fair_share(
        resource_group: String!
        project_id: UUID!
    ): ProjectFairShare

    # User-level Fair Share list
    user_fair_shares(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: UserFairShareFilter
        order: UserFairShareOrderBy
    ): UserFairShareConnection!

    # Specific User's Fair Share detail
    user_fair_share(
        resource_group: String!
        user_uuid: UUID!
        project_id: UUID!  # User can belong to multiple Projects
    ): UserFairShare

    # ─────────────────────────────────────────────────────────────────
    # Usage Bucket Query (for debugging/monitoring, separated by tier)
    # ─────────────────────────────────────────────────────────────────

    # Domain usage buckets
    domain_usage_buckets(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: DomainUsageBucketFilter
        order: DomainUsageBucketOrderBy
    ): DomainUsageBucketConnection!

    # Project usage buckets
    project_usage_buckets(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: ProjectUsageBucketFilter
        order: ProjectUsageBucketOrderBy
    ): ProjectUsageBucketConnection!

    # User usage buckets
    user_usage_buckets(
        resource_group: String!
        first: Int
        last: Int
        before: String
        after: String
        offset: Int
        filter: UserUsageBucketFilter
        order: UserUsageBucketOrderBy
    ): UserUsageBucketConnection!
}

# ScalingGroup type - existing fields preserved
type ScalingGroup {
    # ... existing fields ...
    scheduler: String!
    scheduler_opts: JSONString  # Per-scheduler type config (parsed by client)
}
```

#### Mutation

```graphql
type Mutation {
    # Domain Fair Share Weight Configuration
    upsert_domain_fair_share(
        resource_group: String!
        domain_name: String!
        weight: Decimal!
    ): DomainFairShare!

    # Project Fair Share Weight Configuration
    upsert_project_fair_share(
        resource_group: String!
        project_id: UUID!
        weight: Decimal!
    ): ProjectFairShare!

    # User Fair Share Weight Configuration
    upsert_user_fair_share(
        resource_group: String!
        user_uuid: UUID!
        project_id: UUID!
        weight: Decimal!
    ): UserFairShare!

    # Weight Reset (restore to default 1.0)
    reset_fair_share_weight(
        resource_group: String!
        target_type: FairShareTargetType!  # DOMAIN | PROJECT | USER
        target_id: String!  # domain_name or UUID
    ): Boolean!
}
```

#### Scenario-based Usage Examples

##### Scenario 1: Verify Fair Share Scheduler Configuration

**Purpose**: Check if Fair Share scheduler is configured for the Resource Group and what parameters are set

```graphql
query {
    resource_group(name: "gpu-cluster") {
        name
        scheduler        # Check if "fairshare"
        scheduler_opts   # Fair Share parameters
    }
}
# scheduler_opts example:
# {
#     "half_life_days": 7,      ← 7-day half-life
#     "lookback_days": 28,      ← 28-day usage lookup
#     "decay_unit_days": 1,
#     "default_weight": "1.0",
#     "gap_policy": "interpolate",
#     "max_gap_hours": 24
# }
```

##### Scenario 2: Query and Configure Weight Policy

**Purpose**: Check and configure priority weight per Domain/Project/User

```graphql
# 2-1. Query per-domain Fair Share (weight + calculated values together)
query {
    domain_fair_shares(
        resource_group: "gpu-cluster"
        first: 100
        order: {field: FAIR_SHARE_FACTOR, direction: DESC}
    ) {
        edges {
            node {
                domain_name
                weight               # Configured ratio
                total_decayed_usage  # Calculated usage
                fair_share_factor    # Calculated Factor
                last_calculated_at
            }
        }
        count
    }
}

# 2-2. Query per-project Fair Share
query {
    project_fair_shares(
        resource_group: "gpu-cluster"
        filter: {domain_name: {equals: "research"}}
    ) {
        edges {
            node {
                project_id
                domain_name
                weight
                fair_share_factor
            }
        }
    }
}

# 2-3. Configure Weight (individual)
mutation {
    upsert_domain_fair_share(
        resource_group: "gpu-cluster"
        domain_name: "research"
        weight: "2.0"
    ) {
        domain_name
        weight
        fair_share_factor
    }
}

mutation {
    upsert_project_fair_share(
        resource_group: "gpu-cluster"
        project_id: "550e8400-..."
        weight: "1.5"
    ) {
        project_id
        weight
        fair_share_factor
    }
}

# 2-4. Reset Weight (restore default 1.0)
mutation {
    reset_fair_share_weight(
        resource_group: "gpu-cluster"
        target_type: USER
        target_id: "6ba7b810-..."
    )
}
```

##### Scenario 3: Check Current Scheduling Priority

**Purpose**: Check users' current Fair Share Factor and ranking (for monitoring/dashboard)

```graphql
# 3-1. All users' priority ranking (highest first)
query {
    user_fair_shares(
        resource_group: "gpu-cluster"
        first: 50
        order: {field: FAIR_SHARE_FACTOR, direction: DESC}
    ) {
        edges {
            node {
                user_uuid
                fair_share_factor  # 0~1, higher = higher priority
                rank               # 1st, 2nd, ...
                effective_weight   # Applied Weight (Domain×Project×User)
                effective_usage    # Decay-applied cumulative usage
            }
        }
        count
    }
}

# 3-2. Priority of users in specific domain
query {
    user_fair_shares(
        resource_group: "gpu-cluster"
        filter: {domain_name: {equals: "research"}}
        order: {field: RANK, direction: ASC}
    ) {
        edges {
            node {
                user_uuid
                fair_share_factor
                rank
            }
        }
    }
}

# 3-3. Specific user's current Fair Share info
query {
    user_fair_shares(
        resource_group: "gpu-cluster"
        filter: {user_uuid: {equals: "6ba7b810-..."}}
    ) {
        edges {
            node {
                user_uuid
                fair_share_factor
                rank
                effective_weight
                effective_usage
            }
        }
    }
}
```

##### Scenario 4: Usage History Analysis (Debugging)

**Purpose**: Analyze "Why is this user's priority low?"

```graphql
# 4-1. Query specific user's last 28 days usage buckets
query {
    user_usage_buckets(
        resource_group: "gpu-cluster"
        filter: {user_uuid: {equals: "6ba7b810-..."}}
        first: 28
        order: {field: PERIOD_START, direction: DESC}
    ) {
        edges {
            node {
                period_start          # Bucket start date
                period_end            # Bucket end date
                resource_usage  # {"cpu": 86400, "mem": ...}
            }
        }
    }
}
# Result interpretation:
# - High usage in last 7 days (Period 0) → Low Fair Share Factor
# - Older buckets have reduced impact due to Decay

# 4-2. Query usage for specific period only
query {
    user_usage_buckets(
        resource_group: "gpu-cluster"
        filter: {
            user_uuid: {equals: "6ba7b810-..."}
            period_start: {gte: "2026-01-01"}
            period_end: {lte: "2026-01-07"}
        }
    ) {
        edges {
            node {
                period_start
                resource_usage
            }
        }
    }
}
```

##### Scenario 5: Weight Change Effect Simulation

**Purpose**: Check priority changes before and after weight modification

```graphql
# Step 1: Check current state
query {
    user_fair_shares(resource_group: "gpu-cluster", first: 10) {
        edges {
            node { user_uuid, fair_share_factor, rank, effective_weight }
        }
    }
}

# Step 2: Change weight
mutation {
    upsert_domain_fair_share(
        resource_group: "gpu-cluster"
        domain_name: "research"
        weight: "3.0"
    ) {
        domain_name
        weight
        fair_share_factor
    }
}

# Step 3: Check state after change (research domain users expected to rank higher)
query {
    user_fair_shares(resource_group: "gpu-cluster", first: 10) {
        edges {
            node { user_uuid, fair_share_factor, rank, effective_weight }
        }
    }
}
```

### Admin UI Integration

The Admin UI provides the following features:

1. **Resource Group Settings Page**
   - Scheduler selection (FIFO/LIFO/DRF/FairShare)
   - Fair Share options configuration (half_life, lookback, gap_policy, etc.)

2. **Fair Share Weight Management Page**
   - Per Domain/Project/User weight configuration
   - Hierarchy tree visualization

3. **Fair Share Monitoring Dashboard**
   - Per-user Fair Share Factor ranking
   - Usage history graphs
   - Decay application visualization

## Migration / Compatibility

### Backward Compatibility

- **No impact on existing Sequencers**: FIFO, LIFO, DRF continue to work as before
- **Opt-in approach**: Only activated when `resource_group.scheduler = "fairshare"` is set
- **No existing API changes**: GraphQL/REST API compatibility maintained

### Database Migration

Only adds new tables, does not modify existing tables:

```python
# Alembic migration
def upgrade() -> None:
    # 1. kernel_usage_records table (raw data)
    # Note: No ForeignKey - allows hard delete, orphan cleanup handled separately
    op.create_table(
        "kernel_usage_records",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("kernel_id", GUID(), nullable=False),
        sa.Column("session_id", GUID(), nullable=False),
        sa.Column("user_uuid", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resource_usage", ResourceSlotColumn(), nullable=False),
    )
    op.create_index("ix_kernel_usage_sg_period", "kernel_usage_records", ["resource_group", "period_start"])
    op.create_index("ix_kernel_usage_user_period", "kernel_usage_records", ["user_uuid", "period_start"])
    op.create_index("ix_kernel_usage_kernel_id", "kernel_usage_records", ["kernel_id"])

    # 2. domain_usage_buckets table (Domain aggregation cache)
    # Note: No ForeignKey - allows hard delete
    op.create_table(
        "domain_usage_buckets",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("domain_name", sa.String(64), nullable=False),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("decay_unit_days", sa.Integer(), nullable=False, default=1),
        sa.Column("resource_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint(
        "uq_domain_usage_bucket",
        "domain_usage_buckets",
        ["domain_name", "resource_group", "period_start"]
    )
    op.create_index("ix_domain_usage_bucket_lookup", "domain_usage_buckets", ["domain_name", "resource_group", "period_start"])

    # 3. project_usage_buckets table (Project aggregation cache)
    # Note: No ForeignKey - allows hard delete
    op.create_table(
        "project_usage_buckets",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("decay_unit_days", sa.Integer(), nullable=False, default=1),
        sa.Column("resource_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint(
        "uq_project_usage_bucket",
        "project_usage_buckets",
        ["project_id", "resource_group", "period_start"]
    )
    op.create_index("ix_project_usage_bucket_lookup", "project_usage_buckets", ["project_id", "resource_group", "period_start"])

    # 4. user_usage_buckets table (User aggregation cache)
    # Note: No ForeignKey - allows hard delete
    # User can belong to multiple Projects, so (user_uuid, project_id) combination needed
    op.create_table(
        "user_usage_buckets",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_uuid", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("decay_unit_days", sa.Integer(), nullable=False, default=1),
        sa.Column("resource_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint(
        "uq_user_usage_bucket",
        "user_usage_buckets",
        ["user_uuid", "project_id", "resource_group", "period_start"]
    )
    op.create_index("ix_user_usage_bucket_lookup", "user_usage_buckets", ["user_uuid", "project_id", "resource_group", "period_start"])

    # 5. domain_fair_shares table (Domain state summary)
    op.create_table(
        "domain_fair_shares",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        # Configured value
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=False, default=Decimal("1.0")),
        # Calculated values
        sa.Column("total_decayed_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("normalized_usage", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("0")),
        sa.Column("fair_share_factor", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("1.0")),
        sa.Column("resource_weights", ResourceSlotColumn(), nullable=False),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
        # Calculation parameters (tracks conditions used for calculation)
        sa.Column("lookback_start", sa.Date(), nullable=True),
        sa.Column("lookback_end", sa.Date(), nullable=True),
        sa.Column("half_life_days", sa.Integer(), nullable=True),
        sa.Column("lookback_days", sa.Integer(), nullable=True),
        sa.Column("decay_unit_days", sa.Integer(), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint("uq_domain_fair_share", "domain_fair_shares", ["resource_group", "domain_name"])
    op.create_index("ix_domain_fair_share_lookup", "domain_fair_shares", ["resource_group", "domain_name"])

    # 6. project_fair_shares table (Project state summary)
    op.create_table(
        "project_fair_shares",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        # Configured value
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=False, default=Decimal("1.0")),
        # Calculated values
        sa.Column("total_decayed_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("normalized_usage", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("0")),
        sa.Column("fair_share_factor", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("1.0")),
        sa.Column("resource_weights", ResourceSlotColumn(), nullable=False),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
        # Calculation parameters (tracks conditions used for calculation)
        sa.Column("lookback_start", sa.Date(), nullable=True),
        sa.Column("lookback_end", sa.Date(), nullable=True),
        sa.Column("half_life_days", sa.Integer(), nullable=True),
        sa.Column("lookback_days", sa.Integer(), nullable=True),
        sa.Column("decay_unit_days", sa.Integer(), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint("uq_project_fair_share", "project_fair_shares", ["resource_group", "project_id"])
    op.create_index("ix_project_fair_share_lookup", "project_fair_shares", ["resource_group", "project_id"])

    # 7. user_fair_shares table (User state summary)
    op.create_table(
        "user_fair_shares",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("resource_group", sa.String(64), nullable=False),
        sa.Column("user_uuid", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        # Configured value
        sa.Column("weight", sa.Numeric(precision=10, scale=4), nullable=False, default=Decimal("1.0")),
        # Calculated values
        sa.Column("total_decayed_usage", ResourceSlotColumn(), nullable=False),
        sa.Column("normalized_usage", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("0")),
        sa.Column("fair_share_factor", sa.Numeric(precision=8, scale=6), nullable=False, default=Decimal("1.0")),
        sa.Column("resource_weights", ResourceSlotColumn(), nullable=False),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
        # Calculation parameters (tracks conditions used for calculation)
        sa.Column("lookback_start", sa.Date(), nullable=True),
        sa.Column("lookback_end", sa.Date(), nullable=True),
        sa.Column("half_life_days", sa.Integer(), nullable=True),
        sa.Column("lookback_days", sa.Integer(), nullable=True),
        sa.Column("decay_unit_days", sa.Integer(), nullable=True),
        # Metadata
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    op.create_unique_constraint("uq_user_fair_share", "user_fair_shares", ["resource_group", "user_uuid", "project_id"])
    op.create_index("ix_user_fair_share_lookup", "user_fair_shares", ["resource_group", "user_uuid", "project_id"])

    # 8. Add last_slice_end column to kernels table
    op.add_column("kernels", sa.Column("last_slice_end", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column("kernels", "last_slice_end")
    op.drop_table("user_fair_shares")
    op.drop_table("project_fair_shares")
    op.drop_table("domain_fair_shares")
    op.drop_table("user_usage_buckets")
    op.drop_table("project_usage_buckets")
    op.drop_table("domain_usage_buckets")
    op.drop_table("kernel_usage_records")
```

### Initial State Handling

- **New installations**: Start with empty history (all users equal priority)
- **Existing installations**: Can backfill from past session data (optional)

## Implementation Plan

### Phase 1: Database Schema (BA-3812) - DONE
- [x] Create `KernelUsageRecordRow` model
  - [x] period_start/period_end slice structure
  - [x] user_uuid/project_id based (no access_key usage)
  - [x] resource_usage (allocated resources × time)
  - [x] Relationships setup (kernel, session, user, project, domain)
- [x] Create Usage Bucket models (3 tables per tier)
  - [x] `DomainUsageBucketRow` - domain_name based aggregation
  - [x] `ProjectUsageBucketRow` - project_id based aggregation
  - [x] `UserUsageBucketRow` - (user_uuid, project_id) combination based aggregation
  - [x] resource_usage for Fair Share calculation
  - [x] Mutable bucket strategy (period_end extension, new bucket when exceeding decay_unit)
  - [x] Relationships setup
- [x] Create Fair Share state table models (3 per tier)
  - [x] `DomainFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] `ProjectFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] `UserFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] last_calculated_at timestamp per table
  - [x] Calculation parameter columns (lookback_start/end, half_life_days, lookback_days, decay_unit_days)
- [ ] Add `KernelRow.last_usage_recorded_at` column (renamed from last_slice_end)
- [x] Write Alembic migration
- [x] Implement Repository layer
  - [x] `ResourceUsageHistoryDBSource` / `ResourceUsageHistoryRepository`
  - [x] `FairShareDBSource` / `FairShareRepository`
- [ ] Unit tests

### Phase 2: Fair Share Calculation Service (BA-3063) - TODO
- [ ] Implement `UsageAggregationService`
  - [ ] Slice creation logic (trigger-based, not exact 5-minute intervals)
  - [ ] Use `KernelRow.last_usage_recorded_at` for tracking last measurement
  - [ ] Terminated kernel handling (terminated_at based)
  - [ ] Bucket aggregation logic (UPSERT) - resource_usage only
  - [ ] Cache recalculation logic
- [ ] Implement gap recovery strategy
  - [ ] Apply `gap_policy` configuration (interpolate / ignore)
  - [ ] Apply `max_gap_hours` limit
- [ ] Flat decay calculation logic (Slurm compatible)
- [ ] Background task registration (5-minute cycle)
- [ ] Unit tests

### Phase 3: FairShareSequencer (BA-3064) - TODO
- [ ] Implement `FairShareSequencer` class
  - [ ] Per-resource-group config query
  - [ ] Hierarchical weight calculation (relative ratio without normalization)
  - [ ] Flat decay method (fixed)
- [ ] `FairShareConfig` configuration model (includes gap_policy)
- [ ] `HierarchyWeight` dataclass
- [ ] Register in sequencer pool
- [ ] Integration tests

### Phase 4: API & Integration (BA-3069) - DONE
- [x] Implement REST API
  - [x] Fair Share Weight CRUD
  - [x] Fair Share Status query
- [x] Implement GraphQL API
  - [x] domain_fair_shares/project_fair_shares/user_fair_shares queries
  - [x] upsert_*_fair_share mutations
  - [x] *_usage_buckets queries (for debugging)
- [ ] Admin UI integration
  - [ ] Resource Group settings page
  - [ ] Fair Share Weight management page
  - [ ] Fair Share monitoring dashboard
- [ ] End-to-end tests
- [ ] Performance tests (scheduling latency measurement)
- [ ] Documentation

## Open Questions

### Resolved

1. ~~**Decay Method Selection**~~: Flat vs Continuous
   - **Decision: Use Flat method only** - Computationally efficient + Slurm compatible, minimal result difference

2. ~~**user_usage_buckets Period Fields**~~
   - **Decision: Use period_start/period_end** - Mutable strategy (period_end extension, new bucket when exceeding decay_unit)

3. ~~**Kernel Termination Handling**~~
   - **Decision: Handle in batch aggregation** - terminated_at based

4. ~~**Slice Gap Strategy**~~
   - **Decision: Configuration-based handling** - `gap_policy` (interpolate / ignore)
   - `max_gap_hours` to limit max gap period during long downtime
   - Use `server_started_at` for gap detection on server restart

5. ~~**Per-Resource-Group Config**~~
   - **Decision: FairShareRepository** - Query config at sequence() time

6. ~~**Weight Storage Location**~~
   - **Decision: Integrated in per-tier fair_shares tables** - weight + calculated values (total_decayed_usage, fair_share_factor)
   - Separated into `domain_fair_shares`, `project_fair_shares`, `user_fair_shares`
   - Not added directly to Domain/Group/User tables (entities independent of scheduler)

7. ~~**Share vs Fair Share Factor Concepts**~~
   - **Decision: Clearly distinguish** - Share(Weight) is allocation ratio, Fair Share Factor is priority score

8. ~~**UniqueConstraint Issue**~~
   - **Decision: Remove** - Batch timing differences can cause duplicates, handle with UPSERT

9. ~~**Slice Creation Timing**~~
   - **Decision: Trigger-based** - Based on batch execution time, not exact 5-minute intervals

10. ~~**Calculation Parameter Tracking**~~
    - **Decision: Store calculation parameters in fair_shares table**
    - `lookback_start`, `lookback_end`: Lookup period range
    - `half_life_days`, `lookback_days`, `decay_unit_days`: Configuration values
    - Used to determine if recalculation needed when config changes
    - Provides calculation condition visibility to users

11. ~~**Repository Pattern**~~
    - **Decision: Separate DBSource + Repository** - DB handled directly in DBSource

12. ~~**Kernel Table Change**: Adding usage tracking column~~
    - **Decision: Add `last_usage_recorded_at` column** (renamed from `last_slice_end`)
    - Tracks the timestamp of last usage record creation
    - Column performance is better than querying MAX(period_end) for each kernel
    - Name reflects "usage measurement/recording" rather than internal "slice" concept

13. ~~**Actual Usage Measurement**~~
    - **Decision: Do NOT store `measured_usage` in DB**
    - Only `resource_usage` (allocated × time) is stored for Fair Share calculation
    - Actual measured usage is available via Prometheus metrics
    - Billing claims can be addressed using Prometheus data
    - Rationale: Avoid duplication, Prometheus already handles real-time metrics with proper retention

14. ~~**resource_group → resource_group Naming**~~
    - **Decision: Rename to `resource_group`** throughout all layers
    - More consistent with external API terminology
    - Applied to: Models, Repository, Service, API, Client, DTO layers

### Unresolved

1. **Cross-Resource-Group Usage**: When a user uses multiple resource groups?
   - Current proposal: Independent fair share calculation per resource group
   - Alternative: Track global usage (increases complexity)

2. **Resource Normalization Method**: ResourceSlot → Single metric conversion
   - Current proposal: Use CPU-seconds as default metric
   - Alternative: Per-resource weight configuration like TRES billing weight
   - Need to consider higher weight for GPU resources

3. **Tier Weight Propagation Scope**: Impact of upper tier weight changes
   - Current proposal: Simple multiplication (Domain × Project × User)
   - Alternative: Track per-tier usage separately like Fair Tree

4. **Slice-Bucket Boundary Alignment**: When slices span date boundaries
   - Current proposal: Determine bucket based on `period_start`
   - Precise handling: Split slices at date boundaries

5. **lookback_days Limit**: Whether to limit to multiples of half-life
   - Current proposal: No limit (flexibility)
   - Alternative: decay_depth concept (multiples of half_life)

6. **Rescheduling Scenario**: When a running kernel terminates and gets rescheduled
   - Issue: `started_at`, `terminated_at` can be updated again
   - Current proposal: Use new kernel_id for rescheduled kernels (distinguish from original)
   - Review needed: Detailed design for kernel_id separation
   ```
   Scenario: Kernel rescheduling
   1. Kernel K1 running (started_at=10:00)
   2. 10:15 health check fails → set terminated_at=10:15
   3. 10:16 rescheduled → create new Kernel K2 (started_at=10:16)

   Batch aggregation perspective:
   - Slices until 10:15: Created from original K1 (termination handling)
   - After 10:16: Start separate slices from new K2
   ```

## References

- [Slurm Classic Fair Share Algorithm](https://slurm.schedmd.com/classic_fair_share.html)
- [Slurm Fair Tree Algorithm](https://slurm.schedmd.com/fair_tree.html)
- [Slurm Multifactor Priority Plugin](https://slurm.schedmd.com/priority_multifactor.html)
- [DRF Paper (Ghodsi et al., NSDI 2011)](https://cs.stanford.edu/~matei/papers/2011/nsdi_drf.pdf)
- [Sokovan Scheduler README](../src/ai/backend/manager/sokovan/scheduler/README.md)
- [Sequencers README](../src/ai/backend/manager/sokovan/scheduler/provisioner/sequencers/README.md)
