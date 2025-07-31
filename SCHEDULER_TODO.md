# Scheduler 리팩토링 TODO

## 1. 핵심 스케줄링 로직 구현

### 1.1 스케줄러 플러그인 시스템
- [ ] `load_scheduler()` 함수 구현
- [ ] `load_agent_selector()` 함수 구현
- [ ] 플러그인 로딩 메커니즘 통합
- [ ] ScalingGroupOpts 및 설정 처리

### 1.2 AbstractScheduler 인터페이스 구현
- [ ] `prioritize()` 메서드 구현
- [ ] `pick_session()` 메서드 구현
- [ ] `update_allocation()` 메서드 구현
- [ ] 기존 스케줄러 플러그인들과의 호환성 보장

### 1.3 AbstractAgentSelector 인터페이스 구현
- [ ] `assign_agent_for_session()` 메서드 구현
- [ ] `assign_agent_for_kernel()` 메서드 구현
- [ ] 아키텍처 호환성 체크
- [ ] 컨테이너 제한 필터링

## 2. 데이터 모델 통합

### 2.1 SessionRow ↔ SessionData 변환
- [ ] SessionRow를 SessionData로 변환하는 매퍼 구현
- [ ] SessionData를 SessionRow로 역변환하는 매퍼 구현
- [ ] 중첩된 kernel 데이터 처리

### 2.2 Repository 통합
- [ ] ScheduleRepository 메서드를 도메인별 리포지토리로 분리
- [ ] 트랜잭션 경계 처리
- [ ] 데이터 일관성 보장

## 3. Validator 시스템 개선

### 3.1 Private 세션 처리
- [ ] Validator 실행 시 private 세션 필터링 로직 추가
- [ ] Private 세션은 다음 validator만 실행:
  - ReservedBatchSessionValidator
  - DependenciesValidator
  - ConcurrencyValidator

### 3.2 동시성 카운터 업데이트
- [ ] ConcurrencyValidator에서 Redis 카운터 증가 로직 추가
- [ ] 스케줄링 실패 시 카운터 롤백 메커니즘

### 3.3 Hook 플러그인 지원
- [ ] Validator 체인에 Hook 플러그인 통합
- [ ] HookResult 처리 로직 구현

## 4. 에이전트 할당 로직

### 4.1 Single Node 세션 스케줄링
- [ ] `schedule_single_node_session()` 구현
- [ ] 수동 에이전트 지정 처리
- [ ] 에이전트 리소스 검증
- [ ] 할당 실패 시 롤백

### 4.2 Multi Node 세션 스케줄링
- [ ] `schedule_multi_node_session()` 구현
- [ ] 커널별 개별 에이전트 할당
- [ ] 부분 실패 시 전체 롤백
- [ ] KernelAgentBinding 처리

## 5. 상태 관리 및 이벤트

### 5.1 세션 상태 전이
- [ ] PENDING → SCHEDULED 상태 전이 구현
- [ ] 상태 업데이트 트랜잭션 처리
- [ ] 실패 시 상태 롤백

### 5.2 이벤트 발생
- [ ] SessionScheduledEvent 발생
- [ ] SessionCancelledEvent 발생
- [ ] 이벤트 실패 시 처리

## 6. 동시성 및 트랜잭션

### 6.1 분산 락
- [ ] 스케줄링 프로세스 전체에 대한 락 구현
- [ ] 데드락 방지 메커니즘
- [ ] 락 타임아웃 처리

### 6.2 재시도 로직
- [ ] `retry_txn` 데코레이터 통합
- [ ] `execute_with_retry` 함수 통합
- [ ] 재시도 정책 설정

## 7. 모니터링 및 메트릭

### 7.1 스케줄링 메트릭
- [ ] 스케줄링 시작/종료 마킹
- [ ] 성능 메트릭 수집
- [ ] 실패 원인 추적

### 7.2 로깅 개선
- [ ] 구조화된 로깅 추가
- [ ] 디버깅을 위한 컨텍스트 정보
- [ ] 성능 프로파일링

## 8. 통합 및 마이그레이션

### 8.1 기존 시스템과의 통합
- [ ] SchedulerDispatcher에서 새 Scheduler 호출
- [ ] 점진적 마이그레이션 전략
- [ ] 롤백 계획

### 8.2 테스트
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 성능 테스트
- [ ] 동시성 테스트

## 9. 추가 개선 사항

### 9.1 확장성
- [ ] 새로운 ClusterMode 지원 준비
- [ ] 커스텀 Validator 추가 인터페이스
- [ ] 플러그인 기반 정책 시스템

### 9.2 성능 최적화
- [ ] 데이터 프리페칭 최적화
- [ ] 배치 처리 개선
- [ ] 캐싱 전략

### 9.3 에러 처리
- [ ] 상세한 에러 메시지
- [ ] 에러 복구 메커니즘
- [ ] 사용자 친화적 에러 응답

## 우선순위

1. **긴급**: 데이터 모델 변환 및 기본 스케줄링 로직
2. **높음**: Validator 시스템 완성 및 에이전트 할당
3. **중간**: 상태 관리, 이벤트, 동시성 제어
4. **낮음**: 모니터링, 성능 최적화, 추가 개선사항