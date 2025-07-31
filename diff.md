# Single Node vs Multi Node Session 스케줄링 비교

## 주요 차이점 분석

### 1. 스케줄링 단위
- **Single Node**: 전체 세션을 하나의 에이전트에 할당
- **Multi Node**: 각 커널을 개별적으로 서로 다른 에이전트에 할당 가능

### 2. 리소스 할당 방식

#### Single Node (`_schedule_single_node_session`)
```python
# 세션 전체의 requested_slots를 한 에이전트에 할당
agent_alloc_ctx = await self.schedule_repository.reserve_agent(
    sgroup_name,
    agent_id,
    sess_ctx.requested_slots,  # 전체 세션의 리소스
)
```

#### Multi Node (`_schedule_multi_node_session`)
```python
# 각 커널별로 requested_slots를 개별 할당
for kernel in sess_ctx.kernels:
    agent_alloc_ctx = await self.schedule_repository.reserve_agent(
        sgroup_name,
        agent_id,
        kernel.requested_slots,  # 개별 커널의 리소스
    )
```

### 3. 아키텍처 호환성 검사

#### Single Node
- 모든 커널이 동일한 아키텍처여야 함
- 세션의 메인 커널 아키텍처만 확인
```python
requested_architectures = set(k.architecture for k in sess_ctx.kernels)
if len(requested_architectures) > 1:
    raise GenericBadRequest("Cannot assign multiple kernels with different architectures")
```

#### Multi Node
- 각 커널이 서로 다른 아키텍처를 가질 수 있음
- 커널별로 호환 가능한 에이전트 필터링
```python
for kernel in sess_ctx.kernels:
    compatible_candidate_agents = [
        ag for ag in candidate_agents if ag.architecture == kernel.architecture
    ]
```

### 4. 에이전트 선택 메서드

#### Single Node
```python
agent_id = await agent_selector.assign_agent_for_session(
    compatible_candidate_agents,
    sess_ctx,  # 전체 세션 전달
)
```

#### Multi Node
```python
agent_id = await agent_selector.assign_agent_for_kernel(
    available_candidate_agents,
    kernel,  # 개별 커널 전달
)
```

### 5. 트랜잭션 및 롤백 처리

#### Single Node
- 단일 할당이므로 실패 시 단순 처리
- 예외 발생 시 해당 세션만 실패 처리

#### Multi Node
- 여러 커널 중 하나라도 실패하면 전체 롤백 필요
- `kernel_agent_bindings` 리스트로 성공한 할당 추적
- 모든 커널이 성공한 경우에만 최종 확정

### 6. 실패 처리 메서드

#### Single Node
```python
await self.schedule_repository._update_session_scheduling_failure(
    sched_ctx, sess_ctx, exc.extra_msg
)
```

#### Multi Node
```python
await self.schedule_repository.update_kernel_scheduling_failure(
    sched_ctx, sess_ctx, kernel.id, exc.extra_msg
)
```

### 7. 최종 처리 메서드

#### Single Node
```python
await self.schedule_repository.finalize_single_node_session(
    sess_ctx.id, sgroup_name, agent_alloc_ctx
)
```

#### Multi Node
```python
await self.schedule_repository.finalize_multi_node_session(
    sess_ctx.id, sgroup_name, kernel_agent_bindings
)
```

## 통합 가능성 분석

### 공통점
1. 아키텍처 호환성 검사
2. 에이전트 가용성 확인
3. 리소스 예약 프로세스
4. 실패 시 예외 처리
5. 최종 상태 업데이트 및 이벤트 발생

### 차이점 해결 방안

1. **스케줄링 단위 추상화**
   - Session 또는 Kernel을 모두 처리할 수 있는 일반화된 인터페이스
   - `SchedulableUnit` 같은 추상 개념 도입

2. **리소스 할당 전략 분리**
   - Single: 한 번의 큰 할당
   - Multi: 여러 번의 작은 할당
   - 이를 Strategy 패턴으로 분리

3. **에이전트 선택 통합**
   - `assign_agent_for_session`과 `assign_agent_for_kernel`을 하나의 메서드로
   - 대상 타입에 따라 내부 동작 분기

4. **트랜잭션 관리 일반화**
   - 할당 작업을 리스트로 관리
   - Single Node는 길이 1인 리스트
   - Multi Node는 커널 수만큼의 리스트

## 결론

두 메서드는 본질적으로 동일한 작업(리소스 할당)을 수행하지만, 할당 단위와 트랜잭션 범위가 다릅니다. 이는 다음과 같이 통합 가능합니다:

```python
async def _schedule_session(
    self,
    sched_ctx: SchedulingContext,
    agent_selector: AbstractAgentSelector,
    sgroup_name: str,
    candidate_agents: Sequence[AgentRow],
    sess_ctx: SessionRow,
    check_results: list[tuple[str, Union[Exception, PredicateResult]]],
) -> None:
    # ClusterMode에 따라 스케줄링 단위 결정
    if sess_ctx.cluster_mode == ClusterMode.SINGLE_NODE:
        scheduling_units = [sess_ctx]  # 세션 전체를 하나의 단위로
    else:
        scheduling_units = sess_ctx.kernels  # 각 커널을 개별 단위로
    
    # 공통 스케줄링 로직 적용
    allocations = []
    for unit in scheduling_units:
        # 아키텍처 호환성 검사, 에이전트 선택, 리소스 할당
        allocation = await self._allocate_unit(unit, ...)
        allocations.append(allocation)
    
    # 모든 할당 성공 시 최종 처리
    await self._finalize_allocations(sess_ctx, allocations)
```

이렇게 통합하면 코드 중복을 줄이고 유지보수성을 높일 수 있습니다.