# Background Task Retry 기능 구현 계획

## 개요
BackgroundTaskManager에 Redis 기반 retry 기능을 추가하여, 서버 장애 시에도 작업이 자동으로 재시도될 수 있도록 구현한다.

## 아키텍처 설계

### 1. Redis 데이터 구조

#### 1.1 Task 메타데이터 저장
```
Key: bgtask:task:{task_id}
Type: String (JSON)
Fields:
  - body: JSON serialized task request data
  - status: pending|running|completed|failed
  - created_at: timestamp
  - updated_at: timestamp
  - server_id: 실행 중인 서버 ID
  - server_type: 서버 타입 (manager|storage-proxy)
  - func_name: 실행할 함수 이름
  - retry_count: 재시도 횟수
  - checkpoint: 재개를 위한 중간 상태 (optional)
TTL: 24시간
```

#### 1.2 서버 타입별 Task ID 집합
```
Key: bgtask:server_group:{SERVER_TYPE}
Type: Set
Members: {task_id1, task_id2, ...}
SERVER_TYPE: manager | storage-proxy
Description: 해당 타입의 모든 서버에서 실행 가능한 task들
Examples:
  - bgtask:server_group:manager - 모든 manager 서버가 재시도 가능
  - bgtask:server_group:storage-proxy - 모든 storage-proxy 서버가 재시도 가능
TTL: 24시간 (주기적 갱신)
```

#### 1.3 서버별 Task ID 집합
```
Key: bgtask:server:{server_id}
Type: Set
Members: {task_id1, task_id2, ...}
Description: 특정 서버에서만 실행 가능한 task들
TTL: 24시간 (주기적 갱신)
```

### 2. 주요 컴포넌트

#### 2.1 TaskMetadata 데이터 클래스
```python
@dataclass
class TaskMetadata:
    task_id: uuid.UUID
    func_name: str
    body: dict  # 원본 요청 데이터
    status: TaskStatus
    created_at: float
    updated_at: float
    server_id: Optional[str]
    retry_count: int = 0
    checkpoint: Optional[dict] = None  # 재개 가능한 작업을 위한 체크포인트
```

#### 2.2 TaskRegistry (Redis 작업 관리)
- Task 메타데이터 CRUD
- TTL 관리
- 서버 그룹/서버별 task 집합 관리

#### 2.3 TaskMonitor (Health Check)
- 주기적으로 실행 중인 task들의 TTL 업데이트
- 실패한 task 감지
- 재시도 가능한 task 큐잉

#### 2.4 TaskRecovery (재시도 로직)
- 실패한 task 감지
- 재시도 가능 여부 판단
- Task 재실행

## 구현 상세

### Phase 1: 기본 인프라 구축
1. **TaskMetadata 타입 정의**
   - src/ai/backend/common/bgtask/types.py 생성
   - TaskStatus enum, TaskMetadata dataclass 정의

2. **Redis 연결 설정**
   - BackgroundTaskManager에 Redis client 추가
   - Redis connection 초기화 로직

3. **TaskRegistry 구현**
   - Task 메타데이터 저장/조회/삭제
   - 서버 그룹 및 서버별 task 집합 관리

### Phase 2: Task 실행 및 모니터링
1. **Task 시작 시 Redis 등록**
   - start() 메서드에서 tasㄴk 메타데이터 저장
   - 서버 그룹/서버 ID별 집합에 추가

2. **TTL Heartbeat 메커니즘**
   - 실행 중인 task의 TTL 주기적 갱신 (10분마다)
   - _wrapper_task()에 heartbeat 로직 추가

3. **Task 완료/실패 처리**
   - Task 완료 시 Redis에서 제거 또는 상태 업데이트
   - 실패 시 retry 가능 상태로 표시

### Phase 3: 재시도 메커니즘
1. **TaskMonitor 구현**
   - 백그라운드 task로 주기적 모니터링
   - TTL 만료 임박 task 감지
   - 재시도 큐에 추가

2. **TaskRecovery 구현**
   - 재시도 가능한 task 스캔
   - 서버 그룹/서버 ID 기반 필터링
   - Task 재실행 로직

3. **재시도 정책**
   - 최대 재시도 횟수 설정
   - Exponential backoff
   - 서버별 우선순위

### Phase 4: 재개 가능한 작업 지원 (Future Extension)
1. **Checkpoint 메커니즘**
   - Task 실행 중 중간 상태 저장
   - ProgressReporter에 checkpoint 메서드 추가

2. **Resume 로직**
   - Checkpoint에서 작업 재개
   - BackgroundTask 인터페이스 확장

## 구현 순서

1. **기본 타입 및 Redis 설정** (Week 1)
   - [ ] TaskMetadata 및 관련 타입 정의
   - [ ] Redis client 통합
   - [ ] TaskRegistry 기본 구현

2. **Task 실행 플로우 수정** (Week 1-2)
   - [ ] start() 메서드에 Redis 등록 로직 추가
   - [ ] TTL heartbeat 구현
   - [ ] Task 완료/실패 처리

3. **모니터링 및 재시도** (Week 2-3)
   - [ ] TaskMonitor 백그라운드 작업 구현
   - [ ] TaskRecovery 재시도 로직
   - [ ] 재시도 정책 구현

4. **테스트 및 검증** (Week 3-4)
   - [ ] 단위 테스트 작성
   - [ ] 통합 테스트
   - [ ] 장애 시나리오 테스트

## 고려사항

### 1. 서버별 작업 구분
- **서버 타입별 작업**: server_group:{SERVER_TYPE}에 등록, 같은 타입의 어느 서버에서든 재시도 가능
  - manager: 모든 manager 인스턴스에서 실행 가능한 작업
  - storage-proxy: 모든 storage-proxy 인스턴스에서 실행 가능한 작업
- **서버 종속적 작업**: 특정 server_id에만 등록, 해당 서버에서만 재시도
  - 예: 특정 storage-proxy의 로컬 파일 시스템 작업

### 2. 재시도 안전성
- **Idempotent 작업**: 안전하게 재시도 가능
- **Non-idempotent 작업**: checkpoint 기반 재개 필요

### 3. 성능 고려사항
- Redis 부하 최소화를 위한 배치 처리
- TTL 업데이트 주기 최적화
- 불필요한 Redis 호출 방지

### 4. 확장성
- 재개 가능한 작업을 위한 인터페이스 설계
- 커스텀 재시도 정책 지원
- 모니터링 메트릭 수집

## 테스트 계획

### 단위 테스트
- TaskRegistry CRUD 작업
- TTL heartbeat 로직
- 재시도 정책 계산

### 통합 테스트
- Task 실행 및 Redis 등록
- 서버 장애 시뮬레이션
- 재시도 시나리오

### 부하 테스트
- 대량 task 처리
- Redis 성능 측정
- 재시도 storm 방지

## 향후 개선 사항

1. **Checkpoint/Resume 메커니즘**
   - 대용량 파일 다운로드 중단 후 재개
   - 배치 작업 부분 실패 복구

2. **분산 Lock 메커니즘**
   - 동일 task 중복 실행 방지
   - Redis 기반 분산 lock

3. **메트릭 및 모니터링**
   - 재시도 성공/실패율
   - Task 실행 시간 추적
   - Redis 사용량 모니터링

4. **고급 재시도 정책**
   - Circuit breaker 패턴
   - Rate limiting
   - Priority queue