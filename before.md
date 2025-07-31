# Schedule vs Start 단계 분석

## 1. Schedule 단계 (`schedule()`)

### 주요 역할
- **DB 상태 업데이트**: 세션과 커널에 에이전트 할당 정보를 DB에 기록
- **리소스 예약**: 에이전트의 가용 리소스를 계산하여 점유 표시
- **상태 전이**: PENDING → SCHEDULED

### 세부 동작

1. **세션 선택 및 검증**
   - Predicate 체크 (리소스 제한, 의존성 등)
   - 적합한 에이전트 찾기

2. **리소스 할당 (DB 레벨)**
   ```python
   # reserve_agent() - 에이전트의 occupied_slots 업데이트
   agent_alloc_ctx = await self.schedule_repository.reserve_agent(
       sgroup_name,
       agent_id,
       sess_ctx.requested_slots,
   )
   ```

3. **세션/커널 정보 업데이트**
   ```python
   # finalize_single_node_session() - 커널에 에이전트 정보 할당
   kernel.agent = agent_alloc_ctx.agent_id
   kernel.agent_addr = agent_alloc_ctx.agent_addr
   kernel.status = KernelStatus.SCHEDULED
   ```

4. **이벤트 발생**
   - `SessionScheduledAnycastEvent`
   - `SessionScheduledBroadcastEvent`

### 실제 에이전트와의 통신
- **없음** - 순수하게 DB 업데이트만 수행
- 에이전트는 아직 이 세션/커널의 존재를 모름

## 2. Check Precondition 단계 (`check_precond()`)

### 주요 역할
- **이미지 확인 및 풀**: 에이전트에 필요한 이미지가 있는지 확인
- **상태 전이**: SCHEDULED → PREPARING

### 세부 동작
1. SCHEDULED 상태의 세션들을 PREPARING으로 전이
2. `registry.check_and_pull_images()` 호출하여 이미지 준비

## 3. Start 단계 (`start()`)

### 주요 역할
- **실제 컨테이너 생성**: 에이전트 RPC를 통해 실제 컨테이너 생성
- **상태 전이**: PREPARED → CREATING → RUNNING

### 세부 동작

1. **세션 상태 변경**
   ```python
   # mark_sessions_and_kernels_creating()
   session.status = SessionStatus.CREATING
   kernel.status = KernelStatus.CREATING
   ```

2. **에이전트 RPC 호출**
   ```python
   # registry.start_session() 내부
   # 실제로 에이전트에 create_kernels RPC 호출
   await self._create_kernels(session, kernel_agent_bindings, ...)
   ```

3. **실패 시 처리**
   ```python
   # start_session()에서 예외 발생 시
   async def _mark_session_cancelled() -> None:
       await self.schedule_repository._mark_session_cancelled(
           sched_ctx, session, status_data
       )
   
   # 세션을 CANCELLED 상태로 변경
   # 이미 할당된 리소스 정리
   await self.registry.destroy_session_lowlevel(...)
   ```

## 4. 핵심 차이점

### Schedule
- **목적**: 어떤 에이전트에 할당할지 결정하고 DB에 기록
- **범위**: Manager 내부의 DB 작업만
- **실패 영향**: 다음 스케줄링 라운드에서 재시도 가능
- **롤백**: DB 트랜잭션 롤백으로 충분

### Start
- **목적**: 실제 컨테이너를 에이전트에서 생성
- **범위**: 에이전트와의 네트워크 통신 포함
- **실패 영향**: 세션이 CANCELLED 상태로 전환
- **롤백**: 
  - DB 상태를 CANCELLED로 변경
  - 에이전트의 컨테이너 정리 필요
  - 할당된 리소스 해제

## 5. 상태 전이 흐름

```
PENDING (초기 상태)
   ↓
SCHEDULED (schedule() - DB에만 할당 정보 기록)
   ↓
PREPARING (check_precond() - 이미지 준비)
   ↓
PREPARED (이미지 준비 완료)
   ↓
CREATING (start() - 실제 컨테이너 생성 시작)
   ↓
RUNNING (컨테이너 생성 완료)
   
실패 시:
CREATING → CANCELLED (start() 실패 시)
```

## 6. 설계 의도

이러한 단계 분리는 다음과 같은 이점을 제공합니다:

1. **트랜잭션 분리**: DB 작업(schedule)과 네트워크 작업(start)을 분리
2. **장애 격리**: 에이전트 장애가 스케줄링 로직에 영향을 주지 않음
3. **재시도 가능성**: 각 단계별로 독립적인 재시도 가능
4. **상태 추적**: 세션이 어느 단계에서 실패했는지 명확히 파악 가능

## 7. 문제점

현재 구조의 잠재적 문제:
- Start 단계 실패 시 세션이 즉시 CANCELLED로 전환
- 일시적인 네트워크 오류나 에이전트 부하로 인한 실패도 영구적 실패로 처리
- SCHEDULED 상태에서 재시도 메커니즘이 없음