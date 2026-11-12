# Sokovan handler 테스트 시나리오

## 관련 이슈

- JIRA: BA-3936

## 동기

Sokovan 스케줄러 리팩터링(BA-3936) 이후 handler 의 책임이 명확히 분리됐지만, 이에 대한 체계적인 테스트 커버리지가 부족하다.

현재 문제:
- handler 단위 테스트가 없거나 옛 구현을 기준으로 작성됐다
- Coordinator 와 handler 패턴에 대한 통합 테스트가 부족하다
- 배포와 라우트 handler 테스트가 완전히 빠져 있다
- 상태 전이 검증 로직에 대한 테스트가 부족하다

테스트 시나리오를 명확히 정의하면 다음을 얻는다.
1. handler 마다 책임 범위를 명시적으로 검증한다
2. 회귀 방지를 위한 기준을 세운다
3. 새 handler 를 추가할 때 참고 기준을 제공한다

---

## 현재 테스트 커버리지

### 라인 커버리지 요약 (pants test --test-use-coverage)

```
pants test --force --test-use-coverage --coverage-py-global-report \
  --coverage-py-filter='["ai.backend.manager.sokovan"]' \
  tests/unit/manager/sokovan/::
```

#### 스케줄러 handler 라인 커버리지

| 파일 | 문장 수 | 누락 | 커버리지 | 비고 |
|------|-------|------|-------|-------|
| **scheduler/coordinator.py** | 406 | 406 | **0%** | ❌ 테스트 없음 |
| **scheduler/factory.py** | 68 | 68 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/base.py | 37 | 37 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/lifecycle/check_precondition.py | 52 | 52 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/lifecycle/schedule_sessions.py | 60 | 60 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/lifecycle/start_sessions.py | 51 | 51 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/lifecycle/terminate_sessions.py | 46 | 46 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/lifecycle/deprioritize_sessions.py | 47 | 47 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/maintenance/sweep_sessions.py | 53 | 53 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/promotion/base.py | 39 | 39 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/promotion/promote_to_prepared.py | 38 | 38 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/promotion/promote_to_running.py | 45 | 45 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/promotion/detect_termination.py | 51 | 51 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/promotion/promote_to_terminated.py | 51 | 51 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/kernel/base.py | 30 | 30 | **0%** | ❌ 테스트 없음 |
| scheduler/handlers/kernel/sweep_stale_kernels.py | 46 | 46 | **0%** | ❌ 테스트 없음 |
| scheduler/hooks/registry.py | 34 | 34 | **0%** | ❌ 테스트 없음 |
| scheduler/hooks/status.py | 113 | 113 | **0%** | ❌ 테스트 없음 |
| scheduler/launcher/launcher.py | 201 | 201 | **0%** | ❌ 테스트 없음 |
| scheduler/kernel/state_engine.py | 50 | 50 | **0%** | ❌ 테스트 없음 |
| **Handler Subtotal** | **1,518** | **1,518** | **0%** | |

#### 스케줄러 provisioner 라인 커버리지 (✅ 테스트 충분)

| 파일 | 문장 수 | 누락 | 커버리지 |
|------|-------|------|-------|
| scheduler/provisioner/provisioner.py | 176 | 32 | 82% |
| scheduler/provisioner/selectors/selector.py | 172 | 14 | 92% |
| scheduler/provisioner/selectors/concentrated.py | 28 | 2 | 93% |
| scheduler/provisioner/selectors/dispersed.py | 18 | 2 | 89% |
| scheduler/provisioner/selectors/legacy.py | 18 | 2 | 89% |
| scheduler/provisioner/selectors/roundrobin.py | 13 | 2 | 85% |
| scheduler/provisioner/selectors/utils.py | 19 | 0 | 100% |
| scheduler/provisioner/sequencers/fifo.py | 15 | 0 | 100% |
| scheduler/provisioner/sequencers/lifo.py | 17 | 5 | 71% |
| scheduler/provisioner/sequencers/drf.py | 35 | 1 | 97% |
| **Provisioner Subtotal** | **~500** | **~60** | **~88%** |

#### 배포 handler 라인 커버리지

| 파일 | 문장 수 | 누락 | 커버리지 | 비고 |
|------|-------|------|-------|-------|
| deployment/coordinator.py | 129 | 21 | 84% | 이력 기록만 테스트 |
| deployment/handlers/base.py | 38 | 8 | 79% | Coordinator 에서 간접 호출 |
| deployment/handlers/pending.py | 41 | 8 | 80% | Coordinator 에서 간접 호출 |
| deployment/handlers/replica.py | 40 | 10 | 75% | Coordinator 에서 간접 호출 |
| deployment/handlers/scaling.py | 44 | 11 | 75% | Coordinator 에서 간접 호출 |
| deployment/handlers/reconcile.py | 41 | 11 | 73% | Coordinator 에서 간접 호출 |
| deployment/handlers/destroying.py | 44 | 11 | 75% | Coordinator 에서 간접 호출 |
| deployment/executor.py | 252 | 196 | **22%** | ⚠️ 커버리지 낮음 |
| deployment/deployment_controller.py | 101 | 48 | 52% | |
| **Deployment Subtotal** | **~730** | **~324** | **~56%** |

#### 라우트 handler 라인 커버리지

| 파일 | 문장 수 | 누락 | 커버리지 | 비고 |
|------|-------|------|-------|-------|
| route/coordinator.py | 131 | 21 | 84% | 이력 기록만 테스트 |
| route/handlers/base.py | 42 | 9 | 79% | Coordinator 에서 간접 호출 |
| route/handlers/provisioning.py | 42 | 7 | 83% | Coordinator 에서 간접 호출 |
| route/handlers/health_check.py | 42 | 10 | 76% | Coordinator 에서 간접 호출 |
| route/handlers/running.py | 43 | 11 | 74% | Coordinator 에서 간접 호출 |
| route/handlers/route_eviction.py | 43 | 11 | 74% | Coordinator 에서 간접 호출 |
| route/handlers/terminating.py | 42 | 10 | 76% | Coordinator 에서 간접 호출 |
| route/handlers/service_discovery_sync.py | 48 | 16 | 67% | |
| route/executor.py | 187 | 149 | **20%** | ⚠️ 커버리지 낮음 |
| **Route Subtotal** | **~620** | **~244** | **~61%** |

### 커버리지 격차 요약

| 영역 | 라인 | 커버리지 | 상태 |
|------|-------|----------|--------|
| 스케줄러 handler | 1,518 | **0%** | ❌ 심각 |
| 스케줄러 provisioner | ~500 | ~88% | ✅ 양호 |
| 배포 | ~730 | ~56% | ⚠️ 부분 |
| 라우트 | ~620 | ~61% | ⚠️ 부분 |

**핵심 문제**: 스케줄러 handler 영역의 **1,518 라인이 커버리지 0%** 다

---

### 테스트 수

### Sokovan 스케줄러 (테스트 180개)

| 구성 요소 | 테스트 수 | 테스트 내용 |
|-----------|-----------|--------------|
| **provisioner/selectors** | 61 | 에이전트 선택 전략 (concentrated, dispersed, roundrobin, legacy) |
| **provisioner/validators** | 38 | 자원 한도 검증 (quota, concurrency, dependencies) |
| **provisioner/sequencers** | 16 | 스케줄링 순서 (FIFO, LIFO, DRF) |
| **recorder** | 39 | 이력 기록 |
| **provisioner (root)** | 6 | provisioner 통합, 에이전트 선택 전략 |
| **test_scheduler.py** | 9 | SessionProvisioner 할당 |
| **test_terminate_sessions.py** | 6 | SessionTerminator |

### Sokovan 배포 (테스트 24개)

| 구성 요소 | 테스트 수 | 테스트 내용 |
|-----------|-----------|--------------|
| **revision_generator** | 9 | service 정의 로드, 병합 |
| **definition_generator** | 6 | 모델 정의 registry |
| **route/coordinator_history** | 5 | 라우트 상태 이력 기록 |
| **coordinator_history** | 4 | 배포 상태 이력 기록 |

### Sokovan 스케줄링 controller (테스트 54개)

| 구성 요소 | 테스트 수 | 테스트 내용 |
|-----------|-----------|--------------|
| **validators/test_rules** | 13 | 검증 규칙 |
| **validators/test_scaling_group_filter** | 12 | 자원 그룹 filter |
| **validators/test_mount** | 12 | 마운트 검증 |
| **test_integration** | 10 | 통합 테스트 |
| **preparers/test_cluster** | 7 | 클러스터 준비 |

### Repository 테스트 (테스트 43개)

| 구성 요소 | 테스트 수 | 테스트 내용 |
|-----------|-----------|--------------|
| **scheduler/test_update_with_history** | 18 | 이력과 함께 상태 변경 |
| **scheduler/test_termination** | 12 | 종료 처리 (일부 깨짐) |
| **schedule/test_termination** | 8 | legacy 종료 |
| **schedule/test_fetch_pending_sessions** | 3 | 대기 세션 조회 |
| **scheduler/test_db_source_isolation** | 2 | DB source 격리 |

### 커버리지 격차 분석

#### ❌ 테스트 없음 (심각)

| 영역 | handler | 현재 상태 |
|------|---------|----------------|
| 스케줄러 라이프사이클 | CheckPreconditionLifecycleHandler | **테스트 없음** |
| 스케줄러 라이프사이클 | ScheduleSessionsLifecycleHandler | **테스트 없음** |
| 스케줄러 라이프사이클 | StartSessionsLifecycleHandler | **테스트 없음** |
| 스케줄러 라이프사이클 | TerminateSessionsLifecycleHandler | Terminator 만 테스트 (6개) |
| 스케줄러 라이프사이클 | DeprioritizeSessionsLifecycleHandler | **테스트 없음** |
| 스케줄러 유지보수 | SweepSessionsLifecycleHandler | **테스트 없음** |
| 스케줄러 승격 | PromoteToPreparedPromotionHandler | **테스트 없음** |
| 스케줄러 승격 | PromoteToRunningPromotionHandler | **테스트 없음** |
| 스케줄러 승격 | DetectTerminationPromotionHandler | **테스트 없음** |
| 스케줄러 승격 | PromoteToTerminatedPromotionHandler | **테스트 없음** |
| 스케줄러 커널 | SweepStaleKernelsKernelHandler | **테스트 없음** |
| 스케줄러 | Coordinator | **테스트 없음** |
| 배포 | CheckPendingDeploymentHandler | **테스트 없음** |
| 배포 | CheckReplicaDeploymentHandler | **테스트 없음** |
| 배포 | ScalingDeploymentHandler | **테스트 없음** |
| 배포 | ReconcileDeploymentHandler | **테스트 없음** |
| 배포 | DestroyingDeploymentHandler | **테스트 없음** |
| 배포 | DeploymentCoordinator | 이력 기록만 테스트 (4개) |
| 라우트 | ProvisioningRouteHandler | **테스트 없음** |
| 라우트 | HealthCheckRouteHandler | **테스트 없음** |
| 라우트 | RunningRouteHandler | **테스트 없음** |
| 라우트 | RouteEvictionRouteHandler | **테스트 없음** |
| 라우트 | TerminatingRouteHandler | **테스트 없음** |
| 라우트 | ServiceDiscoverySyncRouteHandler | **테스트 없음** |
| 라우트 | RouteCoordinator | 이력 기록만 테스트 (5개) |

#### ✅ 테스트 충분 (양호)

| 영역 | 테스트 수 | 커버리지 |
|------|-----------|----------|
| 에이전트 selector 전략 | 61 | ✅ 충분 |
| provisioner validator | 38 | ✅ 충분 |
| sequencer | 16 | ✅ 충분 |
| recorder | 39 | ✅ 충분 |
| 스케줄링 controller validator | 37 | ✅ 충분 |

#### ⚠️ 부분 테스트 (부분)

| 영역 | 현재 | 필요 |
|------|---------|--------|
| SessionProvisioner | 할당 테스트 9개 | 검증 흐름 추가 필요 |
| SessionTerminator | 테스트 6개 | 다양한 에러 case 추가 필요 |
| Coordinator 이력 | 테스트 9개 | 실패 분류 테스트 추가 필요 |

### 테스트 디렉터리 구조 (현재)

```
tests/unit/manager/
├── sokovan/
│   ├── scheduler/
│   │   ├── provisioner/
│   │   │   ├── selectors/        # ✅ 61 tests
│   │   │   ├── validators/       # ✅ 38 tests
│   │   │   └── sequencers/       # ✅ 16 tests
│   │   ├── recorder/             # ✅ 39 tests
│   │   ├── test_scheduler.py     # ⚠️ 9 tests (Provisioner only)
│   │   └── test_terminate_sessions.py  # ⚠️ 6 tests
│   │   └── handlers/             # ❌ None
│   ├── deployment/
│   │   ├── definition_generator/ # ⚠️ 6 tests
│   │   ├── revision_generator/   # ⚠️ 9 tests
│   │   ├── route/
│   │   │   └── test_coordinator_history.py  # ⚠️ 5 tests
│   │   ├── test_coordinator_history.py      # ⚠️ 4 tests
│   │   └── handlers/             # ❌ None
│   └── scheduling_controller/
│       ├── validators/           # ✅ 37 tests
│       ├── preparers/            # ✅ 7 tests
│       └── test_integration.py   # ✅ 10 tests
└── repositories/
    ├── scheduler/                # ⚠️ 32 tests
    └── schedule/                 # ⚠️ 11 tests
```

## 현재 설계

### handler 아키텍처 개요

```
sokovan/
├── scheduler/
│   └── handlers/
│       ├── lifecycle/          # Session lifecycle
│       ├── promotion/          # Status promotion
│       ├── maintenance/        # Maintenance
│       └── kernel/             # Kernel level
├── deployment/
│   ├── handlers/               # Deployment lifecycle
│   └── route/
│       └── handlers/           # Route lifecycle
```

### 스케줄러 handler (12개)

| 분류 | handler | 역할 |
|----------|---------|----------------|
| 라이프사이클 | CheckPreconditionLifecycleHandler | 스케줄링 전 조건 검사 (quota, resource policy) |
| 라이프사이클 | ScheduleSessionsLifecycleHandler | 세션과 에이전트 매칭 및 할당 |
| 라이프사이클 | StartSessionsLifecycleHandler | 할당된 세션 시작 (SCHEDULED → PREPARING) |
| 라이프사이클 | TerminateSessionsLifecycleHandler | 세션 종료 처리 |
| 라이프사이클 | DeprioritizeSessionsLifecycleHandler | 재시도 횟수를 초과한 세션의 우선순위 강등 |
| 유지보수 | SweepSessionsLifecycleHandler | 고아 세션 정리 |
| 승격 | PromoteToPreparedPromotionHandler | PULLING → PREPARED 승격 |
| 승격 | PromoteToRunningPromotionHandler | PREPARED → RUNNING 승격 |
| 승격 | DetectTerminationPromotionHandler | 종료 상태 감지 (TERMINATING 세션) |
| 승격 | PromoteToTerminatedPromotionHandler | → TERMINATED 최종 승격 |
| 커널 | SweepStaleKernelsKernelHandler | stale 커널 정리 |

### 배포 handler (5개)

| handler | 역할 |
|---------|----------------|
| CheckPendingDeploymentHandler | PENDING 배포 처리 |
| CheckReplicaDeploymentHandler | 복제본 상태 확인 |
| ScalingDeploymentHandler | scale up/down 처리 |
| ReconcileDeploymentHandler | 상태 불일치 조정 |
| DestroyingDeploymentHandler | 배포 삭제 처리 |

### 라우트 handler (6개)

| handler | 역할 |
|---------|----------------|
| ProvisioningRouteHandler | 라우트 프로비저닝 |
| HealthCheckRouteHandler | 라우트 헬스 체크 |
| RunningRouteHandler | 실행 중인 라우트 관리 |
| RouteEvictionRouteHandler | 라우트 퇴출 처리 |
| TerminatingRouteHandler | 라우트 종료 처리 |
| ServiceDiscoverySyncRouteHandler | 서비스 디스커버리 동기화 |

## 제안 설계

### 테스트 분류 체계

```
tests/unit/manager/sokovan/
├── scheduler/
│   └── handlers/
│       ├── lifecycle/
│       │   ├── test_check_precondition.py
│       │   ├── test_schedule_sessions.py
│       │   ├── test_start_sessions.py
│       │   ├── test_terminate_sessions.py
│       │   ├── test_deprioritize_sessions.py
│       │   └── test_sweep_sessions.py
│       ├── promotion/
│       │   ├── test_promote_to_prepared.py
│       │   ├── test_promote_to_running.py
│       │   ├── test_detect_termination.py
│       │   └── test_promote_to_terminated.py
│       ├── kernel/
│       │   └── test_sweep_stale_kernels.py
│       └── test_coordinator_integration.py
├── deployment/
│   ├── handlers/
│   │   ├── test_check_pending.py
│   │   ├── test_check_replica.py
│   │   ├── test_scaling.py
│   │   ├── test_reconcile.py
│   │   └── test_destroying.py
│   └── route/
│       └── handlers/
│           ├── test_provisioning.py
│           ├── test_health_check.py
│           ├── test_running.py
│           ├── test_route_eviction.py
│           ├── test_terminating.py
│           └── test_service_discovery_sync.py
```

---

## 테스트 시나리오

### 1. 스케줄러 라이프사이클 handler

#### 1.1 CheckPreconditionLifecycleHandler

**목적**: 스케줄링 전 조건 검사 (quota, resource policy, 도메인/프로젝트 설정)

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| CP-001 | 모든 조건 충족 | 유효한 PENDING 세션 | successes 에 포함 |
| CP-002 | quota 초과 | 사용자 quota 100%, 새 세션 요청 | failures 에 포함, status_info="quota-exceeded" |
| CP-003 | 도메인 비활성 | is_active=False 인 도메인의 세션 | failures 에 포함 |
| CP-004 | 프로젝트 비활성 | is_active=False 인 프로젝트의 세션 | failures 에 포함 |
| CP-005 | 자원 정책 위반 | max_vfolder_count 초과 | failures 에 포함 |
| CP-006 | 입력 없음 | 세션 없음 | 빈 결과 반환 |
| CP-007 | 실패 혼합 | 일부 성공, 일부 실패 | 각각 분류 |

#### 1.2 ScheduleSessionsLifecycleHandler

**목적**: 세션과 에이전트 매칭 및 자원 할당

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| SS-001 | 단일 세션 스케줄링 | PENDING 세션 1개, 충분한 에이전트 | successes, 에이전트 할당 |
| SS-002 | 여러 세션 스케줄링 | PENDING 세션 N개, 충분한 에이전트 | 모두 successes |
| SS-003 | 자원 부족 | 세션 요청 > 가용 자원 | failures, status_info="no-available-agent" |
| SS-004 | 지정 에이전트 사용 | designated_agent_ids 설정 | 지정한 에이전트에만 할당 |
| SS-005 | 지정 에이전트 없음 | 존재하지 않는 에이전트 지정 | failures |
| SS-006 | 멀티 커널 세션 | cluster_size > 1 | 모든 커널 할당 |
| SS-007 | 혼합 작업 | GPU, CPU 세션 | 각각 적합한 에이전트에 할당 |
| SS-008 | 우선순위 스케줄링 | 우선순위가 다른 세션 | 높은 우선순위 먼저 |
| SS-009 | starts_at 예약 | 미래 시각 설정 | 예약 시각까지 건너뜀 |
| SS-010 | private 세션 | is_private=True | 전용 에이전트 할당 또는 실패 |

#### 1.3 StartSessionsLifecycleHandler

**목적**: SCHEDULED 세션 시작 트리거

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| ST-001 | 정상 시작 | SCHEDULED 세션 | successes, prepare_session 호출 |
| ST-002 | 에이전트 연결 실패 | 에이전트 접속 불가 | failures |
| ST-003 | image pull 시작 | image 가 없는 에이전트 | PULLING 상태로 전이 |
| ST-004 | image cache 있음 | image 가 있는 에이전트 | PREPARING → PREPARED |
| ST-005 | 멀티 커널 세션 시작 | 멀티 커널 세션 | 모든 커널 시작 |
| ST-006 | 부분 실패 | 일부 커널만 시작 실패 | failures (세션 전체) |

#### 1.4 TerminateSessionsLifecycleHandler

**목적**: TERMINATING 세션의 종료 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| TS-001 | 정상 종료 | TERMINATING 세션 | successes, kernel destroy 호출 |
| TS-002 | 에이전트 LOST | agent status=LOST | successes (강제 종료) |
| TS-003 | container 없음 | container_id=None | successes (DB 변경만) |
| TS-004 | 일부 커널 실패 | 일부 kernel destroy 실패 | 실패한 커널은 재시도 대기 |
| TS-005 | 멀티 커널 세션 종료 | 멀티 커널 세션 | 모든 커널 종료 |
| TS-006 | 이미 종료됨 | 커널이 이미 TERMINATED | skipped |

#### 1.5 DeprioritizeSessionsLifecycleHandler

**목적**: 재시도 횟수를 초과한 세션의 우선순위 강등 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| DP-001 | 우선순위 강등 | DEPRIORITIZING 세션 | PENDING 으로 전이, 우선순위 하락 |
| DP-002 | 이미 최저 우선순위 | priority=0 | CANCELLED 로 전이 |
| DP-003 | 입력 없음 | 세션 없음 | 빈 결과 |

#### 1.6 SweepSessionsLifecycleHandler

**목적**: 고아 세션 정리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| SW-001 | stale PREPARING | PREPARING 상태 > timeout | TERMINATING 으로 전이 |
| SW-002 | stale PULLING | PULLING 상태 > timeout | TERMINATING 으로 전이 |
| SW-003 | 정상 세션 | timeout 미초과 | skipped |
| SW-004 | 커널 없는 세션 | 세션 존재, 커널 0개 | CANCELLED 로 전이 |

---

### 2. 스케줄러 승격 handler

#### 2.1 PromoteToPreparedPromotionHandler

**목적**: image pull 완료를 확인하고 PREPARED 로 승격

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| PP-001 | pull 완료 | 모든 커널 image 준비 | successes, PREPARED 로 전이 |
| PP-002 | pull 진행 중 | 일부 커널 pull 중 | skipped |
| PP-003 | pull 실패 | 에이전트 에러 | failures |
| PP-004 | 멀티 커널 pull | 멀티 커널 세션 | 모든 커널 완료 시 승격 |
| PP-005 | timeout 초과 | PULLING > 15분 | failures (expired) |

#### 2.2 PromoteToRunningPromotionHandler

**목적**: container 생성 완료를 확인하고 RUNNING 으로 승격

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| PR-001 | 생성 완료 | 모든 커널에 container_id 있음 | successes, RUNNING 으로 전이 |
| PR-002 | 생성 진행 중 | container_id=None | skipped |
| PR-003 | 생성 실패 | 에이전트 에러 | failures |
| PR-004 | 멀티 커널 생성 | 멀티 커널 | 모든 커널 완료 시 승격 |
| PR-005 | timeout 초과 | CREATING > 10분 | failures (expired) |
| PR-006 | 부분 실패 | 일부 커널만 생성 | failures (세션 전체) |

#### 2.3 DetectTerminationPromotionHandler

**목적**: TERMINATING 세션의 커널 종료 상태 감지

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| DT-001 | 모든 커널 종료 | 모든 커널 TERMINATED | successes |
| DT-002 | 종료 진행 중 | 일부 커널 TERMINATING | skipped |
| DT-003 | 에이전트 LOST | 에이전트 접속 불가 | successes (강제 완료) |
| DT-004 | 상태 혼합 | 일부 TERMINATED, 일부 RUNNING | skipped |

#### 2.4 PromoteToTerminatedPromotionHandler

**목적**: 세션을 TERMINATED 최종 상태로 전이

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| PT-001 | 정상 종료 | TERMINATING 세션 | TERMINATED, 결과 기록 |
| PT-002 | 에러로 종료 | status_info="error" | TERMINATED, result=ERROR |
| PT-003 | 사용자 취소 | status_info="user-requested" | TERMINATED, result=USER_CANCELLED |

---

### 3. 스케줄러 커널 handler

#### 3.1 SweepStaleKernelsKernelHandler

**목적**: stale RUNNING 커널을 감지하고 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| SK-001 | stale 커널 감지 | last_stat > threshold | 커널 TERMINATING 전이 |
| SK-002 | 정상 커널 | last_stat 최근 | 변화 없음 |
| SK-003 | 에이전트 LOST | 에이전트 접속 불가 | 커널 TERMINATING 전이 |
| SK-004 | container 없음 | container_id=None, RUNNING | 커널 TERMINATED 전이 |

---

### 4. 배포 handler

#### 4.1 CheckPendingDeploymentHandler

**목적**: PENDING 배포 처리와 최초 세션 생성

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| CD-001 | 신규 배포 | PENDING 상태 | PROVISIONING 으로 전이, 세션 생성 요청 |
| CD-002 | 자원 부족 | 가용 자원 없음 | PENDING 유지, 재시도 대기 |
| CD-003 | 설정 에러 | 유효하지 않은 image | FAILED 로 전이 |

#### 4.2 CheckReplicaDeploymentHandler

**목적**: 복제본 수 유지 확인

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| CR-001 | 복제본 정상 | current == desired | 변화 없음 |
| CR-002 | 복제본 부족 | current < desired | scale-up 트리거 |
| CR-003 | 복제본 초과 | current > desired | scale-down 트리거 |
| CR-004 | 비정상 복제본 | 비정상 복제본 존재 | 교체 트리거 |

#### 4.3 ScalingDeploymentHandler

**목적**: 배포 scale up/down 실행

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| SC-001 | scale up | desired_replicas 증가 | 새 세션 생성 |
| SC-002 | scale down | desired_replicas 감소 | 세션 종료 (낮은 우선순위 먼저) |
| SC-003 | 점진적 scaling | 큰 변경 | batch 처리 |
| SC-004 | 자원 부족 상태의 scale up | 가용 자원 없음 | 부분 scale-up, 나머지는 대기 |

#### 4.4 ReconcileDeploymentHandler

**목적**: 상태 불일치 조정

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RC-001 | 세션 상태 불일치 | DB 와 실제 상태 다름 | 상태 동기화 |
| RC-002 | 고아 세션 | 배포 없는 세션 | 세션 종료 |
| RC-003 | 라우트 불일치 | 라우트 없는 복제본 | 라우트 생성 |

#### 4.5 DestroyingDeploymentHandler

**목적**: 배포 삭제 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| DD-001 | 정상 삭제 | DESTROYING 배포 | 모든 세션 종료, DESTROYED 로 전이 |
| DD-002 | 세션 종료 중 | 일부 세션 TERMINATING | DESTROYING 유지, 대기 |
| DD-003 | 강제 삭제 | force=True | 즉시 DESTROYED, 비동기 정리 |

---

### 5. 라우트 handler

#### 5.1 ProvisioningRouteHandler

**목적**: 라우트 최초 프로비저닝

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RP-001 | 정상 프로비저닝 | PROVISIONING 라우트 | 세션 연결, HEALTH_CHECKING 으로 전이 |
| RP-002 | 세션 미준비 | 세션 PREPARING 유지 | PROVISIONING 유지 |
| RP-003 | 세션 실패 | 세션 TERMINATED | FAILED 로 전이 |

#### 5.2 HealthCheckRouteHandler

**목적**: 라우트 헬스 체크 실행

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RH-001 | 헬스 체크 통과 | 엔드포인트 정상 응답 | RUNNING 으로 전이 |
| RH-002 | 헬스 체크 실패 | 엔드포인트 무응답 | 재시도 후 FAILED |
| RH-003 | timeout | 응답 지연 | 재시도 |
| RH-004 | 연속 성공 필요 | success_threshold=3 | 연속 3회 성공 후 전이 |

#### 5.3 RunningRouteHandler

**목적**: 실행 중인 라우트 모니터링

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RR-001 | 정상 상태 | 헬스 체크 통과 | RUNNING 유지 |
| RR-002 | 헬스 체크 실패 | 연속 실패 | UNHEALTHY 로 전이 |
| RR-003 | 세션 종료 | 연결된 세션 TERMINATED | TERMINATING 으로 전이 |
| RR-004 | 트래픽 분배 | weight 변경 | 라우팅 표 갱신 |

#### 5.4 RouteEvictionRouteHandler

**목적**: 비정상 라우트 퇴출

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RE-001 | 퇴출 실행 | UNHEALTHY 라우트 | EVICTING 으로 전이, 트래픽 차단 |
| RE-002 | 대체 라우트 존재 | 다른 정상 라우트 있음 | 트래픽 재분배 |
| RE-003 | 마지막 라우트 | 대체 라우트 없음 | 경고 발생, 서비스 중단 알림 |

#### 5.5 TerminatingRouteHandler

**목적**: 라우트 종료 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| RT-001 | 정상 종료 | TERMINATING 라우트 | TERMINATED 로 전이 |
| RT-002 | 연결 drain | 활성 연결 있음 | drain 완료 대기 |
| RT-003 | 강제 종료 | timeout 초과 | 즉시 TERMINATED |

#### 5.6 ServiceDiscoverySyncRouteHandler

**목적**: 서비스 디스커버리 동기화

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| SD-001 | 라우트 등록 | 새 RUNNING 라우트 | discovery 에 등록 |
| SD-002 | 라우트 등록 해제 | TERMINATED 라우트 | discovery 에서 제거 |
| SD-003 | metadata 변경 | weight 변경 | discovery metadata 갱신 |
| SD-004 | 동기화 실패 | discovery 연결 실패 | 재시도 대기열에 추가 |

---

### 6. Coordinator 통합 테스트

#### 6.1 실패 분류

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| FC-001 | 재시도 필요 | 첫 실패, timeout 미초과 | 재시도 전이 적용 |
| FC-002 | 만료 | timeout 초과 | 만료 전이 적용 |
| FC-003 | 포기 | max_retries 초과 | give_up 전이 적용 |

#### 6.2 hook 실행

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| HE-001 | RUNNING hook | RUNNING 전이 성공 | occupied_slots 변경, event 발행 |
| HE-002 | TERMINATED hook | TERMINATED 전이 성공 | 자원 해제, event 발행 |
| HE-003 | hook 실패 | hook 실행 중 예외 | 로그 기록, 전이는 완료 |

#### 6.3 distributed lock

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|-------|-----------------|
| DL-001 | lock 획득 | 첫 요청 | handler 실행 |
| DL-002 | lock 경합 | 동시 요청 | 하나만 실행, 나머지 대기 |
| DL-003 | lock timeout | 긴 대기 | timeout 후 다음 cycle 에 재시도 |

---

## 마이그레이션 / 호환성

### 하위 호환성
- 기존 테스트는 유지하되 새 패턴으로 점진적으로 이전한다
- mock 기반 단위 테스트와 실제 DB 기반 통합 테스트를 병행한다

### 하위 호환성을 깨는 변경
- 없음 (테스트 코드 추가만 있다)

## 구현 계획

### Phase 1: 테스트 인프라 구성
1. 테스트 디렉터리 구조 생성
2. 공통 fixture 정의 (mock repository, mock launcher 등)
3. 테스트 데이터 factory 생성

### Phase 2: 스케줄러 handler 테스트
1. 라이프사이클 handler 테스트 (6개)
2. 승격 handler 테스트 (4개)
3. 커널 handler 테스트 (1개)
4. Coordinator 통합 테스트

### Phase 3: 배포 handler 테스트
1. 배포 handler 테스트 (5개)
2. 라우트 handler 테스트 (6개)

### Phase 4: E2E 시나리오 테스트
1. 전체 세션 라이프사이클 테스트
2. 배포 scaling 시나리오
3. 실패 복구 시나리오

## 열린 질문

1. mock 과 Real DB 의 비율 결정
   - 단위 테스트: mock 기반
   - 통합 테스트: 실제 DB (PostgreSQL testcontainer)
   repository 테스트와 component 테스트에서만 Real DB 를 사용할 계획이다

2. 외부 의존성(agent RPC) 테스트 방법
   - mock agent client 사용
   - 필요하면 통합 테스트에서 실제 agent 사용

3. 비동기 event 검증 방법
   - EventProducer mock 으로 발행 event 캡처
   - assertion 으로 event 내용 검증

## 참고

- [BEP-1029: Sokovan Observer Handler](BEP-1029-sokovan-observer-handler.md)
- [BEP-1030: Sokovan Scheduler Status Transition](BEP-1030-sokovan-scheduler-status-transition.md)
- [BA-3936: Scheduling Coordinator Integration](https://lablup.atlassian.net/browse/BA-3936)
