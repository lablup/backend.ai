# fair share scheduler

## 관련 이슈

- JIRA Epic: [BA-3060](https://lablup.atlassian.net/browse/BA-3060) - Sokovan 을 위한 fair share scheduler 구현
- JIRA 스토리:
  - [BA-3812](https://lablup.atlassian.net/browse/BA-3812) - 자원 사용량 테이블
  - [BA-3063](https://lablup.atlassian.net/browse/BA-3063) - fair share 계산 service
  - [BA-3064](https://lablup.atlassian.net/browse/BA-3064) - FairShareSequencer plugin
  - [BA-3860](https://lablup.atlassian.net/browse/BA-3860) - BEP 문서

## 동기

### DRF(Dominant Resource Fairness)의 현재 한계

현재 Sokovan scheduler 의 DRFSequencer 는 **현재 점유한 자원**만으로 우선순위를 정한다:

```python
# DRFSequencer - Only considers currently occupied resources
for access_key, occupancy in system_snapshot.resource_occupancy.by_keypair.items():
    dominant_share = self._calculate_dominant_share(
        occupancy.occupied_slots,  # Only considers currently occupied resources
        system_snapshot.total_capacity
    )
```

이 방식의 문제는 다음과 같다:

| 시나리오 | 사용자 A | 사용자 B | DRF 결과 |
|---------|--------|--------|----------|
| 현재 점유율 | 10% | 10% | 같은 우선순위 |
| 어제 사용량 | 10% | 90% | **반영하지 않음** |
| 공정성 | 적절함 | **불공정함** | DRF 는 구분하지 못함 |

### 이력 기반 fair share 의 필요성

**시간 기반 fair share** 는 HPC(High-Performance Computing) 환경에서 사용하는 표준 스케줄링 정책이다:

1. **단기간 집중 사용 남용 방지**: 과거에 자원을 적게 사용한 사용자에게 많이 사용한 사용자보다 높은 우선순위를 준다
2. **시간 감쇠**: 최근 사용량에 더 높은 가중치를 적용해 오래된 사용 이력의 영향을 줄인다
3. **업계 표준**: Slurm, PBS, LSF 같은 주요 HPC scheduler 가 채택했다

### 사용 사례

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

## 현재 설계

### WorkloadSequencer 인터페이스

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

### 현재 DRFSequencer 구현

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

### SystemSnapshot 구조

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

### sequencer 등록 방식

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

## 제안 설계

### 1. fair share 알고리즘

#### Slurm 방식 반감기 감쇠 수식

**fair share 계수 계산:**
```
F = 2^(-UH / S)

Where:
- F: Fair Share Factor (0.0 ~ 1.0, higher = higher priority)
- UH: Effective Historical Usage (cumulative usage with time decay applied)
- S: Share Allocation (allocated resource ratio, default 1.0)
```

**유효 이력 사용량 계산:**
```
UH = U_current + (D × U_last) + (D² × U_prev) + (D³ × U_prev2) + ...

Where:
- U_i: Resource usage for the i-th period (processor × seconds)
- D: Decay Factor = 2^(-bucket_unit / half_life)
- bucket_unit: Aggregation unit (e.g., 1 day)
- half_life: Half-life (default: 7 days)
```

#### 감쇠 계산 방식: Flat(고정)

**두 방식 비교:**

| 방식 | 설명 | 복잡도 | Slurm 호환 |
|------|------|--------|------------|
| **Flat** | 반감기 구간마다 같은 가중치 | O(periods) | ✓ |
| Continuous | 날짜 단위 연속 감쇠 | O(days) | ✗ |

**Flat 방식만 사용(Slurm 호환):**

Continuous 방식과 Flat 방식의 실제 스케줄링 결과 차이는 작고 Flat 계산이 더 효율적이다.
따라서 **Flat 방식만** 구현하며 설정 항목으로 만들지 않는다.

```
Period 0 (0-7 days):    Weight 1.0
Period 1 (7-14 days):   Weight 0.5
Period 2 (14-21 days):  Weight 0.25
Period 3 (21-28 days):  Weight 0.125
```

**시간 감쇠 시각화:**
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

**Flat 방식을 선택한 이유:**
- 업계 표준 호환을 위해 Slurm 과 같은 방식을 사용한다
- 계산이 효율적이다(28일 계산: 28 → 4)
- Continuous 와 실제 스케줄링 결과 차이가 작다
- 구현과 디버깅이 단순하다

#### 여러 자원 정규화

**문제: 여러 자원 종류**

Backend.AI 는 CPU, 메모리, GPU 등 여러 자원 종류를 관리하므로 fair share 계산이 서로 다른 자원 차원을 다뤄야 한다.

**검토한 접근:**

| 접근 | 설명 | 장점 | 단점 |
|----------|-------------|------|------|
| **SLURM TRESBillingWeights** | 자원을 하나의 과금 단위로 합친다 | 계산이 단순하다 | 가중치를 세심하게 조정해야 한다 |
| **Usage-based Normalization** | `UserUsage / TotalClusterUsage` | 업계 표준(SLURM) | cluster 사용률이 낮을 때 불공정하다 |
| **Capacity-based Normalization** | `UserUsage / ClusterCapacity` | 사용률과 무관하게 공정하다 | 용량 추적이 필요하다 |

**선택한 접근: 자원별 용량 기반 정규화**

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

**용량 기반이 사용량 기반보다 나은 이유:**

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

**자원별 가중치 설정:**

자원별 가중치는 `resource_groups.scheduler_opts` 에 설정한다:

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

**계산 예(1일 구간):**

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

**경계 사례: 용량 0**

어떤 자원의 용량이 0 이거나 사용할 수 없을 때(예: 모든 agent 오프라인):

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

**용량 추적 전략:**

agent 추가, 제거처럼 cluster 용량이 바뀌어도 fair share 계산을 안정적으로 유지하려고 usage bucket 은 생성 시점에 **capacity_snapshot** 을 저장한다:

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

### 2. 2계층 저장 구조

#### 구조 개요

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

#### 저장소 역할 분리

| 테이블 | 역할 | 보존 기간 | 재계산 |
|--------|------|-----------|--------|
| kernel_usage_records | 원본 데이터(기준이 되는 값) | lookback_days | 필요 없음 |
| *_usage_buckets | 구간 단위 집계 캐시 | decay_unit 기준 | 감쇠 설정이 바뀔 때 |
| *_fair_shares | 상태 요약과 가중치 설정 | 영구 | batch 가 갱신 |

#### 성능 분리 전략

| 연산 | 주기 | 내용 | 복잡도 |
|------|------|------|--------|
| 스케줄링 | 1초 | fair_shares 테이블에서 캐시된 계수를 읽는다 | O(pending_users) |
| batch 집계 | 5분 | raw → buckets → fair_shares 갱신 | O(kernels) |
| 캐시 재계산 | 설정이 바뀔 때 | raw 에서 모든 bucket 을 다시 생성한다 | O(records) |

### 3. 데이터베이스 스키마

#### KernelRow 확장

마지막 사용량 측정 시각을 추적하도록 `last_usage_recorded_at` column 을 추가한다:

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

#### kernel_usage_records 테이블

kernel 의 구간별 사용량 slice 를 저장하는 원본 데이터 테이블이다.

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

**구간 slice 예:**
```
Kernel K1 (started: 10:00, terminated: 10:23)
├── Record 1: period_start=10:00, period_end=10:05 (5 min)
├── Record 2: period_start=10:05, period_end=10:10 (5 min)
├── Record 3: period_start=10:10, period_end=10:15 (5 min)
├── Record 4: period_start=10:15, period_end=10:20 (5 min)
└── Record 5: period_start=10:20, period_end=10:23 (3 min, terminated)
```

**자원 사용량 정규화(resource-seconds):**

`resource_usage` 는 **자원량 × 기간(초)** 단위로 저장한다.
이 정규화로 실행 시간이 다른 kernel 들의 사용량을 단순 합산할 수 있다.

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

**kernel 여러 개 합산 예:**
```
User A's kernels (2026-01-13):
├── Kernel 1 (10:00~10:30): {"cpu": 9000, "mem": 18000, "cuda.shares": 1800}
├── Kernel 2 (10:15~10:45): {"cpu": 3600, "mem": 5400, "cuda.shares": 5400}
└── Kernel 3 (14:00~15:00): {"cpu": 7200, "mem": 3600}

Daily sum (time-span independent, simple sum):
{"cpu": 19800, "mem": 27000, "cuda.shares": 7200}
```

**과금 환산:**
- CPU 시간: `cpu-seconds / 3600`
- GPU 시간: `cuda.shares-seconds / 3600`

#### usage bucket 테이블(계층별 집계)

decay unit 구간마다 집계한 사용량 캐시다. 계층마다 테이블 3개로 나뉜다.
감쇠 설정이 바뀌면 kernel_usage_records 에서 다시 계산한다.

**계층 구조:**
```
DomainUsageBucket     (domain_name, resource_group, period)
    └── ProjectUsageBucket  (project_id, domain_name, resource_group, period)
            └── UserUsageBucket   (user_uuid, project_id, domain_name, resource_group, period)
```

**참고:** 사용자는 여러 project 에 속할 수 있으므로 UserUsageBucket 은 `(user_uuid, project_id, domain_name, resource_group, period_start)` 조합으로 유일하게 식별한다.

##### domain_usage_buckets 테이블

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

##### project_usage_buckets 테이블

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

##### user_usage_buckets 테이블

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

**bucket 갱신 전략(가변 + period_end 연장):**

bucket 은 생성 후 `decay_unit_days` 를 넘을 때까지 `period_end` 를 계속 연장하고, 넘으면 새 bucket 을 생성한다.

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

**불변 조건**: `period_end - period_start < decay_unit_days`

**bucket 상태:**
- `period_end - period_start < decay_unit_days`: 현재 활성 bucket(갱신 중)
- `period_end - period_start >= decay_unit_days - 1`: 완료된 bucket(더 이상 갱신하지 않음)

**캐시 재계산 조건:**
- `decay_unit_days` 설정이 바뀔 때(bucket 경계 변경)
- 데이터 정합성 문제가 생겼을 때

### 4. 구간 slice 생성 방식

#### slice 생성 방식

batch 집계 service 는 실행 중인 kernel 과 최근 종료된 kernel 의 slice 를 주기적으로 생성한다.
종료된 kernel 은 batch 작업에서 `terminated_at` 을 기준으로 함께 처리한다.

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

#### 종료된 kernel 처리

**별도 event handler 가 필요 없다:** Coordinator 가 kernel 상태를 변경할 때 `terminated_at` 만 설정하면 되고, 마지막 slice 는 다음 batch 집계에서 자동으로 생성된다.

```python
# When kernel terminates in Coordinator (existing logic)
kernel.status = KernelStatus.TERMINATED
kernel.terminated_at = datetime.now(timezone.utc)
# Do not change last_slice_end → handled by batch

# Automatically processed during batch aggregation
# Kernels with terminated_at > last_slice_end → final slice created
```

#### slice 공백 전략

**원칙: 공백을 허용하고 설정으로 처리**

서버 중단 중 사용량을 완벽히 복구할 수 없고 fair share 는 상대 우선순위를 다루므로 작은 오차는 허용한다. 공백 처리 정책은 설정(`gap_policy`)으로 정한다.

| 설정 | 설명 | 동작 |
|--------|------|------|
| `interpolate` | 서버가 계속 실행 중이었다고 보고 보간한다 | 공백 구간 전체를 slice 하나로 생성한다 |
| `ignore` | 알 수 없는 구간을 집계에서 제외한다 | 공백 구간을 0 으로 본다 |

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

**slice 생성 시점:**
- **트리거 기반**: batch scheduler 가 실행할 때 slice 를 생성한다
- 5분 간격을 정확히 맞추지 않고 batch 실행 시점에 마지막 slice 이후 구간을 집계한다
- 그래서 4분 55초에서 5분 5초처럼 조금씩 달라질 수 있다(허용한다)

**서버 재시작 시 공백 감지:**

서버가 재시작하면 마지막 slice 와 현재 시각 사이에 큰 공백이 생길 수 있다.
이를 감지하려고 `server_started_at`(서버 시작 시각)을 사용한다.

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

**공백 처리 흐름:**
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

**손실을 허용하는 근거:**
- fair share 는 상대 우선순위를 정하는 데 사용한다
- 모든 사용자에게 같은 손실이 생기면 상대 공정성은 유지된다
- 인프라 문제 등 여러 이유로 손실이 생길 수 있다
- 손실 감지 로그는 디버깅용이며 alert 는 필요 없다

**설정 예:**
```python
# resource_groups.scheduler_opts
{
    "gap_policy": "interpolate",  # or "ignore"
    "max_gap_hours": 24,          # Max gap period for interpolate (hours)
}
```

#### slice 와 bucket 의 연결

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

### 5. fair share 개념 정의

#### share 와 fair share 계수

fair share 스케줄링에서 사용하는 두 가지 핵심 개념이다:

| 개념 | 이름 | 설명 | 설정 | 영향 |
|------|------|------|-----------|------|
| **Share** | Allocation Weight | 사용자에게 배정한 자원 할당 비율 | admin 이 설정한다 | 같은 사용량에서 share 가 높으면 우선순위가 높다 |
| **Fair Share Factor** | fair share 계수 | 지난 사용량으로 정한 현재 우선순위 | 자동 계산한다 | 계수가 높으면 우선순위가 높다 |

**수식:**
```
Fair Share Factor = 2^(-Effective_Usage / Share)

- Share (S): Allocated ratio (product of weights)
- Effective Usage (UH): Cumulative usage with time decay applied
- Fair Share Factor (F): Final priority score (0 ~ 1)
```

**예:**
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

**용어:**
- **Share/Weight**: admin 이 설정하는 "할당 비율"
- **Fair Share Factor**: 시스템이 계산하는 "현재 우선순위"
- **Effective Usage**: 감쇠를 적용한 "유효 사용량"

#### 계층적 share 구조

share(가중치)는 Domain → Project → User 계층 구조로 적용한다.

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

#### 유효 share 계산

```
User's Effective Share = Domain_weight × Project_weight × User_weight
                        ─────────────────────────────────────────────
                              Σ(All Users' weight products)

Example:
- Domain A (weight=2), Project 2 (weight=3), User 3 (weight=2)
- Effective Share = (2 × 3 × 2) / Total = 12 / Total
```

### 6. FairShareSequencer 구현

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

### 7. batch 집계 service

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

### 8. sequencer 등록

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

### 9. 계층별 share(가중치) 저장 구조

#### 설계 원칙

share(가중치)는 **resource group 단위로 관리한다**:
- 가중치는 scheduler 유형에 따라 필요할 수도 있고 아닐 수도 있다
- fair share scheduler 를 사용하는 resource group 에서만 의미가 있다
- Domain, Group, User 테이블에 직접 추가하지 않는다(scheduler 와 무관한 entity)

#### fair share 테이블(계층별 상태 요약)

usage bucket 과 별도로 entity 마다 **현재 fair share 상태**를 저장하는 테이블이다.
사용자가 볼 수 있도록 가중치(설정 값)와 계산 값(decayed_usage, factor)을 함께 저장한다.

**테이블 구조 개요:**
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

##### domain_fair_shares 테이블

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

##### project_fair_shares 테이블

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

##### user_fair_shares 테이블

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

**사용 예:**
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

#### FairShareRepository 구현

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

## 설정

### 설정 파라미터(resource group 단위)

`resource_groups.scheduler_opts` JSONB column 에 저장한다.

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `half_life_days` | int | 7 | 사용량 반감기(일). 7일 지난 사용량의 가중치는 50% 다 |
| `lookback_days` | int | 28 | 조회 기간(일). 반감기의 배수를 권장한다 |
| `decay_unit_days` | int | 1 | bucket 집계 단위(일) |
| `slice_interval_seconds` | int | 300 | slice 생성 주기(초) |
| `default_weight` | Decimal | 1.0 | 기본 가중치(계층에 설정이 없을 때) |
| `gap_policy` | SliceGapPolicy | "interpolate" | slice 공백 처리 정책: "interpolate" 또는 "ignore" |
| `max_gap_hours` | int | 24 | interpolate 의 최대 공백 기간(시간) |

### 계층별 가중치 설정

`domain_fair_shares`, `project_fair_shares`, `user_fair_shares` 테이블에서 resource group 단위로 관리한다.

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

### resource group 설정 예

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

### 감쇠 설정이 바뀔 때 동작

`decay_unit_days` 나 `half_life_days` 가 바뀌면:
1. `user_usage_buckets` 캐시를 무효화한다(resource group 단위)
2. `kernel_usage_records` 원본 데이터에서 bucket 을 다시 생성한다
3. 스케줄링을 멈추지 않아도 된다(캐시 재생성 중에는 원본을 직접 조회할 수 있다)

### scheduler 유형별 설정 파싱(enum 기반 union)

`scheduler_opts` JSONB 필드를 scheduler 유형에 따라 다른 타입으로 파싱한다.

#### scheduler 유형 정의

```python
class SchedulerType(StrEnum):
    """Scheduler types."""
    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIRSHARE = "fairshare"
```

#### scheduler별 설정 타입

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

#### 설정 파싱 함수

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

#### 사용 예

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

#### 장점

1. **타입 안전성**: scheduler별 설정에 타입이 분명히 붙는다
2. **JSONB 유지**: 스키마를 변경하지 않고 기존 `scheduler_opts` column 을 사용한다
3. **쉬운 확장**: 새 scheduler 의 타입만 추가한다
4. **IDE 지원**: 자동 완성과 타입 에러 감지를 사용할 수 있다

## API 설계

### REST API

#### resource group fair share 설정 조회, 수정

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

#### fair share 가중치 관리

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

#### 사용자 fair share 계수 조회(읽기 전용)

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

#### 타입 정의

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

##### fair share 가중치(admin 설정)

admin 이 설정하는 가중치 정책 데이터다(DB 에 저장한다).

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

##### fair share(계층별 상태)

batch 가 주기적으로 계산하는 우선순위 정보다(5분마다 갱신하고 `*_fair_shares` 테이블에 저장한다).
계층별로 weight, effective_usage, fair_share_factor, rank 를 담는다.

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

##### usage bucket(계층별 이력)

구간 단위 사용 이력이다(집계한 데이터를 DB 에 저장한다).

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

#### filter 타입

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

#### order 타입

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

#### input 타입

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

#### query

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

#### mutation

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

#### 시나리오별 사용 예

##### 시나리오 1: fair share scheduler 설정 확인

**목적**: resource group 에 fair share scheduler 가 설정됐는지와 어떤 파라미터가 설정됐는지 확인한다

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

##### 시나리오 2: 가중치 정책 조회, 설정

**목적**: Domain, Project, User 단위 우선순위 가중치를 확인하고 설정한다

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

##### 시나리오 3: 현재 스케줄링 우선순위 확인

**목적**: 사용자의 현재 fair share 계수와 순위를 확인한다(모니터링, dashboard 용)

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

##### 시나리오 4: 사용 이력 분석(디버깅)

**목적**: "이 사용자의 우선순위가 왜 낮은가"를 분석한다

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

##### 시나리오 5: 가중치 변경 효과 시뮬레이션

**목적**: 가중치를 변경하기 전과 후의 우선순위 변화를 확인한다

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

### Admin UI 연동

Admin UI 는 다음 기능을 제공한다:

1. **resource group 설정 페이지**
   - scheduler 선택(FIFO/LIFO/DRF/FairShare)
   - fair share 옵션 설정(half_life, lookback, gap_policy 등)

2. **fair share 가중치 관리 페이지**
   - Domain, Project, User 단위 가중치 설정
   - 계층 트리 시각화

3. **fair share 모니터링 dashboard**
   - 사용자별 fair share 계수 순위
   - 사용 이력 그래프
   - 감쇠 적용 시각화

## 마이그레이션 / 호환성

### 하위 호환성

- **기존 sequencer 에 영향 없음**: FIFO, LIFO, DRF 는 이전처럼 동작한다
- **선택 적용 방식**: `resource_group.scheduler = "fairshare"` 를 설정했을 때만 활성화한다
- **기존 API 변경 없음**: GraphQL, REST API 호환성을 유지한다

### 데이터베이스 migration

새 테이블만 추가하고 기존 테이블은 변경하지 않는다:

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

### 초기 상태 처리

- **신규 설치**: 빈 이력으로 시작한다(모든 사용자의 우선순위가 같다)
- **기존 설치**: 과거 session 데이터로 백필할 수 있다(선택)

## 구현 계획

### 1단계: 데이터베이스 스키마(BA-3812) - 완료
- [x] `KernelUsageRecordRow` 모델 생성
  - [x] period_start, period_end slice 구조
  - [x] user_uuid, project_id 기반(access_key 를 사용하지 않는다)
  - [x] resource_usage(할당 자원 × 시간)
  - [x] relationship 설정(kernel, session, user, project, domain)
- [x] usage bucket 모델 생성(계층마다 3개 테이블)
  - [x] `DomainUsageBucketRow` - domain_name 기반 집계
  - [x] `ProjectUsageBucketRow` - project_id 기반 집계
  - [x] `UserUsageBucketRow` - (user_uuid, project_id) 조합 기반 집계
  - [x] fair share 계산용 resource_usage
  - [x] 가변 bucket 전략(period_end 연장, decay_unit 초과 시 새 bucket)
  - [x] relationship 설정
- [x] fair share 상태 테이블 모델 생성(계층마다 3개)
  - [x] `DomainFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] `ProjectFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] `UserFairShareRow` - weight + total_decayed_usage + fair_share_factor
  - [x] 테이블마다 last_calculated_at 시각
  - [x] 계산 파라미터 column(lookback_start, lookback_end, half_life_days, lookback_days, decay_unit_days)
- [ ] `KernelRow.last_usage_recorded_at` column 추가(last_slice_end 에서 이름 변경)
- [x] Alembic migration 작성
- [x] repository 계층 구현
  - [x] `ResourceUsageHistoryDBSource` / `ResourceUsageHistoryRepository`
  - [x] `FairShareDBSource` / `FairShareRepository`
- [ ] 단위 테스트

### 2단계: fair share 계산 service(BA-3063) - 미완료
- [ ] `UsageAggregationService` 구현
  - [ ] slice 생성 로직(트리거 기반, 정확한 5분 간격 아님)
  - [ ] 마지막 측정 추적에 `KernelRow.last_usage_recorded_at` 사용
  - [ ] 종료된 kernel 처리(terminated_at 기준)
  - [ ] bucket 집계 로직(UPSERT), resource_usage 만
  - [ ] 캐시 재계산 로직
- [ ] 공백 복구 전략 구현
  - [ ] `gap_policy` 설정 적용(interpolate / ignore)
  - [ ] `max_gap_hours` 제한 적용
- [ ] Flat 감쇠 계산 로직(Slurm 호환)
- [ ] background task 등록(5분 주기)
- [ ] 단위 테스트

### 3단계: FairShareSequencer(BA-3064) - 미완료
- [ ] `FairShareSequencer` 클래스 구현
  - [ ] resource group 단위 설정 조회
  - [ ] 계층 가중치 계산(정규화 없는 상대 비율)
  - [ ] Flat 감쇠 방식(고정)
- [ ] `FairShareConfig` 설정 모델(gap_policy 포함)
- [ ] `HierarchyWeight` dataclass
- [ ] sequencer pool 에 등록
- [ ] 통합 테스트

### 4단계: API, 연동(BA-3069) - 완료
- [x] REST API 구현
  - [x] fair share 가중치 CRUD
  - [x] fair share 상태 조회
- [x] GraphQL API 구현
  - [x] domain_fair_shares, project_fair_shares, user_fair_shares query
  - [x] upsert_*_fair_share mutation
  - [x] *_usage_buckets query(디버깅용)
- [ ] Admin UI 연동
  - [ ] resource group 설정 페이지
  - [ ] fair share 가중치 관리 페이지
  - [ ] fair share 모니터링 dashboard
- [ ] 종단 간 테스트
- [ ] 성능 테스트(스케줄링 지연 측정)
- [ ] 문서

## 열린 질문

### 해결됨

1. ~~**감쇠 방식 선택**~~: Flat 과 Continuous
   - **결정: Flat 방식만 사용한다**. 계산이 효율적이고 Slurm 과 호환되며 결과 차이가 작다

2. ~~**user_usage_buckets 의 구간 필드**~~
   - **결정: period_start, period_end 를 사용한다**. 가변 전략(period_end 연장, decay_unit 초과 시 새 bucket)

3. ~~**kernel 종료 처리**~~
   - **결정: batch 집계에서 처리한다**. terminated_at 기준

4. ~~**slice 공백 전략**~~
   - **결정: 설정으로 처리한다**. `gap_policy`(interpolate, ignore)
   - 긴 중단 중 최대 공백 기간을 `max_gap_hours` 로 제한한다
   - 서버 재시작 시 공백 감지에 `server_started_at` 을 사용한다

5. ~~**resource group 단위 설정**~~
   - **결정: FairShareRepository**. sequence() 시점에 설정을 조회한다

6. ~~**가중치 저장 위치**~~
   - **결정: 계층별 fair_shares 테이블에 함께 저장한다**. weight 와 계산 값(total_decayed_usage, fair_share_factor)
   - `domain_fair_shares`, `project_fair_shares`, `user_fair_shares` 로 나눈다
   - Domain, Group, User 테이블에 직접 추가하지 않는다(scheduler 와 무관한 entity)

7. ~~**share 와 fair share 계수 개념**~~
   - **결정: 분명히 구분한다**. Share(가중치)는 할당 비율이고 fair share 계수는 우선순위 점수다

8. ~~**UniqueConstraint 문제**~~
   - **결정: 제거한다**. batch 시점 차이로 중복이 생길 수 있어 UPSERT 로 처리한다

9. ~~**slice 생성 시점**~~
   - **결정: 트리거 기반**. batch 실행 시각을 기준으로 하고 정확한 5분 간격을 사용하지 않는다

10. ~~**계산 파라미터 추적**~~
    - **결정: fair_shares 테이블에 계산 파라미터를 저장한다**
    - `lookback_start`, `lookback_end`: 조회 기간 범위
    - `half_life_days`, `lookback_days`, `decay_unit_days`: 설정 값
    - 설정이 바뀔 때 재계산 필요 여부를 판단하는 데 사용한다
    - 사용자에게 계산 조건을 보여준다

11. ~~**repository 패턴**~~
    - **결정: DBSource 와 Repository 를 분리한다**. DB 처리는 DBSource 가 직접 맡는다

12. ~~**kernel 테이블 변경**: 사용량 추적 column 추가~~
    - **결정: `last_usage_recorded_at` column 을 추가한다**(`last_slice_end` 에서 이름 변경)
    - 마지막 사용량 기록 생성 시각을 추적한다
    - kernel 마다 MAX(period_end) 를 조회하는 것보다 column 성능이 좋다
    - 이름이 내부 "slice" 개념이 아니라 "사용량 측정, 기록"을 나타낸다

13. ~~**실제 사용량 측정**~~
    - **결정: DB 에 `measured_usage` 를 저장하지 않는다**
    - fair share 계산용으로 `resource_usage`(할당 × 시간)만 저장한다
    - 실제 측정 사용량은 Prometheus 지표로 확인한다
    - 과금 근거는 Prometheus 데이터로 다룰 수 있다
    - 근거: 중복을 피하고 Prometheus 가 이미 실시간 지표를 적절한 보존 기간으로 다룬다

14. ~~**resource_group → resource_group 이름**~~
    - **결정: 모든 계층에서 `resource_group` 으로 이름을 변경한다**
    - 외부 API 용어와 더 일관된다
    - 모델, repository, service, API, client, DTO 계층에 적용한다

### 미해결

1. **resource group 을 넘는 사용량**: 사용자가 여러 resource group 을 사용할 때의 처리 방법에 대한 결정이 필요하다
   - 현재 제안: resource group 마다 fair share 를 독립적으로 계산한다
   - 대안: 전역 사용량을 추적한다(복잡도가 높아진다)

2. **자원 정규화 방식**: ResourceSlot 을 단일 지표로 환산한다
   - 현재 제안: CPU-seconds 를 기본 지표로 사용한다
   - 대안: TRES billing weight 처럼 자원별 가중치를 설정한다
   - GPU 자원에 더 높은 가중치를 둘 필요가 있다

3. **계층 가중치 전파 범위**: 상위 계층 가중치 변경의 영향
   - 현재 제안: 단순 곱셈(Domain × Project × User)
   - 대안: Fair Tree 처럼 계층별 사용량을 따로 추적한다

4. **slice 와 bucket 경계 정렬**: slice 가 날짜 경계를 걸칠 때
   - 현재 제안: `period_start` 로 bucket 을 정한다
   - 정밀 처리: 날짜 경계에서 slice 를 나눈다

5. **lookback_days 제한**: 반감기의 배수로 제한하는 방식을 검토한다
   - 현재 제안: 제한하지 않는다(유연성)
   - 대안: decay_depth 개념(half_life 의 배수)

6. **재스케줄링 시나리오**: 실행 중인 kernel 이 종료되고 다시 스케줄링될 때
   - 문제: `started_at`, `terminated_at` 이 다시 갱신될 수 있다
   - 현재 제안: 다시 스케줄링된 kernel 에 새 kernel_id 를 사용한다(원래 kernel 과 구분한다)
   - 검토 필요: kernel_id 분리 상세 설계
   ```
   Scenario: Kernel rescheduling
   1. Kernel K1 running (started_at=10:00)
   2. 10:15 health check fails → set terminated_at=10:15
   3. 10:16 rescheduled → create new Kernel K2 (started_at=10:16)

   Batch aggregation perspective:
   - Slices until 10:15: Created from original K1 (termination handling)
   - After 10:16: Start separate slices from new K2
   ```

## 참고

- [Slurm 클래식 fair share 알고리즘](https://slurm.schedmd.com/classic_fair_share.html)
- [Slurm Fair Tree 알고리즘](https://slurm.schedmd.com/fair_tree.html)
- [Slurm 다중 요인 우선순위 plugin](https://slurm.schedmd.com/priority_multifactor.html)
- [DRF 논문(Ghodsi 등, NSDI 2011)](https://cs.stanford.edu/~matei/papers/2011/nsdi_drf.pdf)
- [Sokovan scheduler README](../src/ai/backend/manager/sokovan/scheduler/README.md)
- [sequencer README](../src/ai/backend/manager/sokovan/scheduler/provisioner/sequencers/README.md)
