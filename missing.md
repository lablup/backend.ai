# Missing Functionality in scheduler.py

## 누락된 주요 기능들

### 1. 스케줄러 로딩 및 초기화
- `load_scheduler()` 함수 누락 - 플러그인 시스템을 통한 스케줄러 로딩
- `load_agent_selector()` 함수 누락 - 플러그인 시스템을 통한 에이전트 선택기 로딩
- ScalingGroupOpts 및 스케줄러 설정 처리 누락

### 2. 스케줄링 핵심 로직
- `prioritize()` - 우선순위 기반 세션 필터링 누락
- `pick_session()` - 실제 세션 선택 로직 누락 (현재는 단순히 첫 번째 세션 반환)
- `update_allocation()` - 스케줄링 후 내부 상태 업데이트 누락

### 3. 에이전트 선택 및 할당
- 에이전트 선택 로직 완전 누락
- Single Node vs Multi Node 세션 처리 분기 누락
- 에이전트 필터링 (아키텍처, 컨테이너 제한 등) 누락
- 리소스 예약 및 할당 로직 누락

### 4. Predicate 검사 시스템
- Hook 플러그인을 통한 추가 predicate 검사 누락
- Private 세션에 대한 특별 처리 누락 (validators에서는 구현됨)
- Predicate 실패 시 재시도 로직 누락

### 5. 이벤트 및 상태 관리
- 세션 상태 전이 (PENDING -> SCHEDULED) 처리 누락
- 이벤트 발생 (SessionScheduledEvent 등) 누락
- 스케줄링 실패 시 상태 업데이트 누락

### 6. 트랜잭션 및 동시성 제어
- 분산 락 메커니즘 누락
- 재시도 로직 (`retry_txn`, `execute_with_retry`) 누락
- 트랜잭션 롤백 처리 누락

### 7. 기타 기능들
- 세션 취소 처리 (`_flush_cancelled_sessions`) 누락
- 컨테이너 제한 확인 (`_filter_agent_by_container_limit`) 누락
- 스케줄러 타이머 및 주기적 실행 누락
- 스케줄링 메트릭 수집 및 마킹 누락

## Validator 구현 분석

### 완료된 Validator 변환
모든 predicate 함수들이 validator 클래스로 성공적으로 변환됨:
- ✅ `check_reserved_batch_session` → `ReservedBatchSessionValidator`
- ✅ `check_concurrency` → `ConcurrencyValidator`
- ✅ `check_dependencies` → `DependenciesValidator`
- ✅ `check_keypair_resource_limit` → `KeypairResourceLimitValidator`
- ✅ `check_user_resource_limit` → `UserResourceLimitValidator`
- ✅ `check_group_resource_limit` → `GroupResourceLimitValidator`
- ✅ `check_domain_resource_limit` → `DomainResourceLimitValidator`
- ✅ `check_pending_session_count_limit` → `PendingSessionCountLimitValidator`
- ✅ `check_pending_session_resource_limit` → `PendingSessionResourceLimitValidator`

### Validator 구현의 차이점

1. **에러 처리 방식**
   - 기존: `PredicateResult(passed=False, message="...")` 반환
   - 신규: 예외 발생 (`SchedulerValidationError` 서브클래스)

2. **데이터 접근 방식**
   - 기존: 직접 DB 쿼리 수행
   - 신규: ValidatorContext를 통한 사전 로드된 데이터 사용

3. **Concurrency 체크의 Redis 연동**
   - 기존: `registry.valkey_stat.check_keypair_concurrency()` 직접 호출
   - 신규: `context.keypair_concurrency_used`로 이미 로드된 값 사용
   - ⚠️ Redis 증가 로직이 누락됨 (동시성 카운터 업데이트 필요)

4. **Private 세션 처리**
   - 기존: `_check_predicates()`에서 private 세션은 일부 validator 제외
   - 신규: 각 validator 내부에서 처리 필요 (현재 ConcurrencyValidator만 구현)

5. **Group 이름 처리**
   - 기존: `check_group_resource_limit`에서 group_id만 표시
   - 신규: `GroupResourceLimitValidator`에서 group_name 표시 (개선됨)

## 데이터 구조 및 타입 차이

### 1. SessionRow vs SessionData
- dispatcher.py는 SQLAlchemy 모델(SessionRow) 직접 사용
- scheduler.py는 데이터 클래스(SessionData) 사용
- 변환 로직 필요

### 2. SchedulingContext
- dispatcher.py의 SchedulingContext는 registry와 known_slot_types만 포함
- 새로운 구조에서는 더 많은 컨텍스트 정보 필요

### 3. PredicateResult vs Exception
- 기존: PredicateResult 객체 반환
- 신규: 예외 발생 방식
- 호출 측에서 예외 처리 로직 필요

## 리포지토리 패턴 차이
- dispatcher.py는 ScheduleRepository 직접 사용
- scheduler.py는 여러 도메인별 리포지토리 사용 (SessionRepository, UserRepository 등)
- 메서드 매핑 필요