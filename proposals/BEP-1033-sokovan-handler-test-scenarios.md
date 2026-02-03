---
Author: Hyeokjin Jeon (achimnol@lablup.com)
Status: Draft
Created: 2025-01-19
Created-Version: 25.3.0
Target-Version:
Implemented-Version:
---

# Sokovan Handler Test Scenarios

## Related Issues

- JIRA: BA-3936

## Motivation

Sokovan 스케줄러 리팩토링(BA-3936) 이후 핸들러들의 책임이 명확히 분리되었으나, 이에 대한 체계적인 테스트 커버리지가 부족하다.

현재 문제점:
- 핸들러 단위 테스트가 부재하거나 구 구현 기준으로 작성됨
- Coordinator-Handler 패턴의 통합 테스트 미비
- Deployment/Route 핸들러 테스트 전무
- 상태 전이(Status Transition) 검증 로직 테스트 부족

테스트 시나리오를 명확히 정의하여:
1. 각 핸들러의 책임 범위를 명시적으로 검증
2. 회귀 방지를 위한 기준선 확보
3. 새로운 핸들러 추가 시 참조 가이드 제공

---

## Current Test Coverage

### Line Coverage Summary (pants test --test-use-coverage)

```
pants test --force --test-use-coverage --coverage-py-global-report \
  --coverage-py-filter='["ai.backend.manager.sokovan"]' \
  tests/unit/manager/sokovan/::
```

#### Scheduler Handler Line Coverage

| 파일 | Stmts | Miss | Cover | 비고 |
|------|-------|------|-------|------|
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
| **Handler 소계** | **1,518** | **1,518** | **0%** | |

#### Scheduler Provisioner Line Coverage (✅ 잘 테스트됨)

| 파일 | Stmts | Miss | Cover |
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
| **Provisioner 소계** | **~500** | **~60** | **~88%** |

#### Deployment Handler Line Coverage

| 파일 | Stmts | Miss | Cover | 비고 |
|------|-------|------|-------|------|
| deployment/coordinator.py | 129 | 21 | 84% | History 기록만 |
| deployment/handlers/base.py | 38 | 8 | 79% | Coordinator에서 간접 호출 |
| deployment/handlers/pending.py | 41 | 8 | 80% | Coordinator에서 간접 호출 |
| deployment/handlers/replica.py | 40 | 10 | 75% | Coordinator에서 간접 호출 |
| deployment/handlers/scaling.py | 44 | 11 | 75% | Coordinator에서 간접 호출 |
| deployment/handlers/reconcile.py | 41 | 11 | 73% | Coordinator에서 간접 호출 |
| deployment/handlers/destroying.py | 44 | 11 | 75% | Coordinator에서 간접 호출 |
| deployment/executor.py | 252 | 196 | **22%** | ⚠️ 낮은 커버리지 |
| deployment/deployment_controller.py | 101 | 48 | 52% | |
| **Deployment 소계** | **~730** | **~324** | **~56%** |

#### Route Handler Line Coverage

| 파일 | Stmts | Miss | Cover | 비고 |
|------|-------|------|-------|------|
| route/coordinator.py | 131 | 21 | 84% | History 기록만 |
| route/handlers/base.py | 42 | 9 | 79% | Coordinator에서 간접 호출 |
| route/handlers/provisioning.py | 42 | 7 | 83% | Coordinator에서 간접 호출 |
| route/handlers/health_check.py | 42 | 10 | 76% | Coordinator에서 간접 호출 |
| route/handlers/running.py | 43 | 11 | 74% | Coordinator에서 간접 호출 |
| route/handlers/route_eviction.py | 43 | 11 | 74% | Coordinator에서 간접 호출 |
| route/handlers/terminating.py | 42 | 10 | 76% | Coordinator에서 간접 호출 |
| route/handlers/service_discovery_sync.py | 48 | 16 | 67% | |
| route/executor.py | 187 | 149 | **20%** | ⚠️ 낮은 커버리지 |
| **Route 소계** | **~620** | **~244** | **~61%** |

### 커버리지 Gap 요약

| 영역 | 라인 수 | 커버리지 | 상태 |
|------|---------|----------|------|
| Scheduler Handlers | 1,518 | **0%** | ❌ Critical |
| Scheduler Provisioner | ~500 | ~88% | ✅ Good |
| Deployment | ~730 | ~56% | ⚠️ Partial |
| Route | ~620 | ~61% | ⚠️ Partial |

**핵심 문제**: Scheduler Handler 영역 **1,518 라인이 0% 커버리지**

---

### 테스트 개수

### Sokovan Scheduler (180 tests)

| 컴포넌트 | 테스트 수 | 테스트 내용 |
|----------|----------|------------|
| **provisioner/selectors** | 61 | Agent selection 전략 (concentrated, dispersed, roundrobin, legacy) |
| **provisioner/validators** | 38 | 리소스 제한 검증 (quota, concurrency, dependencies) |
| **provisioner/sequencers** | 16 | 스케줄링 순서 (FIFO, LIFO, DRF) |
| **recorder** | 39 | History 기록 |
| **provisioner (root)** | 6 | Provisioner 통합, agent selection strategy |
| **test_scheduler.py** | 9 | SessionProvisioner allocation |
| **test_terminate_sessions.py** | 6 | SessionTerminator |

### Sokovan Deployment (24 tests)

| 컴포넌트 | 테스트 수 | 테스트 내용 |
|----------|----------|------------|
| **revision_generator** | 9 | Service definition 로드, merge |
| **definition_generator** | 6 | Model definition registry |
| **route/coordinator_history** | 5 | Route 상태 history 기록 |
| **coordinator_history** | 4 | Deployment 상태 history 기록 |

### Sokovan Scheduling Controller (54 tests)

| 컴포넌트 | 테스트 수 | 테스트 내용 |
|----------|----------|------------|
| **validators/test_rules** | 13 | 검증 규칙 |
| **validators/test_scaling_group_filter** | 12 | 스케일링 그룹 필터 |
| **validators/test_mount** | 12 | 마운트 검증 |
| **test_integration** | 10 | 통합 테스트 |
| **preparers/test_cluster** | 7 | 클러스터 준비 |

### Repository Tests (43 tests)

| 컴포넌트 | 테스트 수 | 테스트 내용 |
|----------|----------|------------|
| **scheduler/test_update_with_history** | 18 | History 포함 상태 업데이트 |
| **scheduler/test_termination** | 12 | 종료 처리 (일부 broken) |
| **schedule/test_termination** | 8 | Legacy termination |
| **schedule/test_fetch_pending_sessions** | 3 | Pending 세션 조회 |
| **scheduler/test_db_source_isolation** | 2 | DB source 격리 |

### 커버리지 Gap 분석

#### ❌ 테스트 없음 (Critical)

| 영역 | Handler | 현재 상태 |
|------|---------|-----------|
| Scheduler Lifecycle | CheckPreconditionLifecycleHandler | **테스트 없음** |
| Scheduler Lifecycle | ScheduleSessionsLifecycleHandler | **테스트 없음** |
| Scheduler Lifecycle | StartSessionsLifecycleHandler | **테스트 없음** |
| Scheduler Lifecycle | TerminateSessionsLifecycleHandler | Terminator만 테스트 (6개) |
| Scheduler Lifecycle | DeprioritizeSessionsLifecycleHandler | **테스트 없음** |
| Scheduler Maintenance | SweepSessionsLifecycleHandler | **테스트 없음** |
| Scheduler Promotion | PromoteToPreparedPromotionHandler | **테스트 없음** |
| Scheduler Promotion | PromoteToRunningPromotionHandler | **테스트 없음** |
| Scheduler Promotion | DetectTerminationPromotionHandler | **테스트 없음** |
| Scheduler Promotion | PromoteToTerminatedPromotionHandler | **테스트 없음** |
| Scheduler Kernel | SweepStaleKernelsKernelHandler | **테스트 없음** |
| Scheduler | Coordinator | **테스트 없음** |
| Deployment | CheckPendingDeploymentHandler | **테스트 없음** |
| Deployment | CheckReplicaDeploymentHandler | **테스트 없음** |
| Deployment | ScalingDeploymentHandler | **테스트 없음** |
| Deployment | ReconcileDeploymentHandler | **테스트 없음** |
| Deployment | DestroyingDeploymentHandler | **테스트 없음** |
| Deployment | DeploymentCoordinator | History 기록만 테스트 (4개) |
| Route | ProvisioningRouteHandler | **테스트 없음** |
| Route | HealthCheckRouteHandler | **테스트 없음** |
| Route | RunningRouteHandler | **테스트 없음** |
| Route | RouteEvictionRouteHandler | **테스트 없음** |
| Route | TerminatingRouteHandler | **테스트 없음** |
| Route | ServiceDiscoverySyncRouteHandler | **테스트 없음** |
| Route | RouteCoordinator | History 기록만 테스트 (5개) |

#### ✅ 잘 테스트됨 (Good)

| 영역 | 테스트 수 | 커버리지 |
|------|----------|----------|
| Agent Selector 전략 | 61 | ✅ 충분 |
| Provisioner Validators | 38 | ✅ 충분 |
| Sequencers | 16 | ✅ 충분 |
| Recorder | 39 | ✅ 충분 |
| Scheduling Controller Validators | 37 | ✅ 충분 |

#### ⚠️ 부분적 테스트 (Partial)

| 영역 | 현재 | 필요 |
|------|------|------|
| SessionProvisioner | allocation 9개 | validation flow 추가 필요 |
| SessionTerminator | 6개 | 다양한 에러 케이스 추가 필요 |
| Coordinator History | 9개 | failure classification 테스트 필요 |

### 테스트 디렉토리 구조 (현재)

```
tests/unit/manager/
├── sokovan/
│   ├── scheduler/
│   │   ├── provisioner/
│   │   │   ├── selectors/        # ✅ 61 tests
│   │   │   ├── validators/       # ✅ 38 tests
│   │   │   └── sequencers/       # ✅ 16 tests
│   │   ├── recorder/             # ✅ 39 tests
│   │   ├── test_scheduler.py     # ⚠️ 9 tests (Provisioner만)
│   │   └── test_terminate_sessions.py  # ⚠️ 6 tests
│   │   └── handlers/             # ❌ 없음
│   ├── deployment/
│   │   ├── definition_generator/ # ⚠️ 6 tests
│   │   ├── revision_generator/   # ⚠️ 9 tests
│   │   ├── route/
│   │   │   └── test_coordinator_history.py  # ⚠️ 5 tests
│   │   ├── test_coordinator_history.py      # ⚠️ 4 tests
│   │   └── handlers/             # ❌ 없음
│   └── scheduling_controller/
│       ├── validators/           # ✅ 37 tests
│       ├── preparers/            # ✅ 7 tests
│       └── test_integration.py   # ✅ 10 tests
└── repositories/
    ├── scheduler/                # ⚠️ 32 tests
    └── schedule/                 # ⚠️ 11 tests
```

## Current Design

### Handler 구조 개요

```
sokovan/
├── scheduler/
│   └── handlers/
│       ├── lifecycle/          # 세션 생명주기
│       ├── promotion/          # 상태 승격
│       ├── maintenance/        # 유지보수
│       └── kernel/             # 커널 레벨
├── deployment/
│   ├── handlers/               # 디플로이먼트 생명주기
│   └── route/
│       └── handlers/           # 라우트 생명주기
```

### Scheduler Handlers (12개)

| Category | Handler | 책임 |
|----------|---------|------|
| Lifecycle | CheckPreconditionLifecycleHandler | 스케줄링 전 조건 검사 (quota, 리소스 정책) |
| Lifecycle | ScheduleSessionsLifecycleHandler | 세션-에이전트 매칭 및 할당 |
| Lifecycle | StartSessionsLifecycleHandler | 할당된 세션 시작 (SCHEDULED → PREPARING) |
| Lifecycle | TerminateSessionsLifecycleHandler | 세션 종료 처리 |
| Lifecycle | DeprioritizeSessionsLifecycleHandler | 재시도 초과 세션 우선순위 하락 |
| Maintenance | SweepSessionsLifecycleHandler | 고아 세션 정리 |
| Promotion | PromoteToPreparedPromotionHandler | PULLING → PREPARED 승격 |
| Promotion | PromoteToRunningPromotionHandler | PREPARED → RUNNING 승격 |
| Promotion | DetectTerminationPromotionHandler | 종료 상태 감지 (TERMINATING 세션) |
| Promotion | PromoteToTerminatedPromotionHandler | → TERMINATED 최종 승격 |
| Kernel | SweepStaleKernelsKernelHandler | Stale 커널 정리 |

### Deployment Handlers (5개)

| Handler | 책임 |
|---------|------|
| CheckPendingDeploymentHandler | PENDING 디플로이먼트 처리 |
| CheckReplicaDeploymentHandler | 레플리카 상태 체크 |
| ScalingDeploymentHandler | 스케일 업/다운 처리 |
| ReconcileDeploymentHandler | 상태 불일치 조정 |
| DestroyingDeploymentHandler | 디플로이먼트 삭제 처리 |

### Route Handlers (6개)

| Handler | 책임 |
|---------|------|
| ProvisioningRouteHandler | 라우트 프로비저닝 |
| HealthCheckRouteHandler | 라우트 헬스체크 |
| RunningRouteHandler | 실행 중 라우트 관리 |
| RouteEvictionRouteHandler | 라우트 퇴출 처리 |
| TerminatingRouteHandler | 라우트 종료 처리 |
| ServiceDiscoverySyncRouteHandler | 서비스 디스커버리 동기화 |

## Proposed Design

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

## Test Scenarios

### 1. Scheduler Lifecycle Handlers

#### 1.1 CheckPreconditionLifecycleHandler

**목적**: 스케줄링 전 조건 검사 (quota, 리소스 정책, 도메인/그룹 설정)

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| CP-001 | 모든 조건 충족 | 유효한 PENDING 세션 | successes에 포함 |
| CP-002 | Quota 초과 | 사용자 quota 100%, 새 세션 요청 | failures에 포함, status_info="quota-exceeded" |
| CP-003 | 도메인 비활성화 | is_active=False인 도메인의 세션 | failures에 포함 |
| CP-004 | 그룹 비활성화 | is_active=False인 그룹의 세션 | failures에 포함 |
| CP-005 | 리소스 정책 위반 | max_vfolder_count 초과 | failures에 포함 |
| CP-006 | 빈 입력 | 세션 없음 | 빈 결과 반환 |
| CP-007 | 복합 실패 | 일부 성공, 일부 실패 | 각각 분류됨 |

#### 1.2 ScheduleSessionsLifecycleHandler

**목적**: 세션-에이전트 매칭 및 리소스 할당

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| SS-001 | 단일 세션 스케줄링 | 1 PENDING 세션, 충분한 에이전트 | successes, 에이전트 할당됨 |
| SS-002 | 다중 세션 스케줄링 | N개 PENDING 세션, 충분한 에이전트 | 모두 successes |
| SS-003 | 리소스 부족 | 세션 요청 > 가용 리소스 | failures, status_info="no-available-agent" |
| SS-004 | 지정 에이전트 사용 | designated_agent_ids 설정 | 지정된 에이전트에만 할당 |
| SS-005 | 지정 에이전트 부재 | 없는 에이전트 지정 | failures |
| SS-006 | 클러스터 세션 | cluster_size > 1 | 모든 커널 할당됨 |
| SS-007 | 혼합 워크로드 | GPU + CPU 세션 | 각각 적합한 에이전트에 할당 |
| SS-008 | 우선순위 스케줄링 | priority 다른 세션들 | 높은 우선순위 먼저 |
| SS-009 | starts_at 예약 | 미래 시간 설정 | 시간 전까지 skipped |
| SS-010 | Private 세션 | is_private=True | 전용 에이전트 또는 실패 |

#### 1.3 StartSessionsLifecycleHandler

**목적**: SCHEDULED 세션 시작 트리거

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| ST-001 | 정상 시작 | SCHEDULED 세션 | successes, prepare_session 호출됨 |
| ST-002 | 에이전트 연결 실패 | 에이전트 unreachable | failures |
| ST-003 | 이미지 풀링 시작 | 이미지 없는 에이전트 | PULLING 상태로 전환 |
| ST-004 | 이미지 캐시 존재 | 이미지 있는 에이전트 | PREPARING → PREPARED |
| ST-005 | 클러스터 시작 | 다중 커널 세션 | 모든 커널 시작 |
| ST-006 | 부분 실패 | 일부 커널만 시작 실패 | failures (전체 세션) |

#### 1.4 TerminateSessionsLifecycleHandler

**목적**: TERMINATING 세션 종료 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| TS-001 | 정상 종료 | TERMINATING 세션 | successes, 커널 destroy 호출 |
| TS-002 | 에이전트 LOST | 에이전트 상태=LOST | successes (강제 종료) |
| TS-003 | 컨테이너 없음 | container_id=None | successes (DB만 업데이트) |
| TS-004 | 부분 커널 실패 | 일부 커널 destroy 실패 | 실패 커널 재시도 대기 |
| TS-005 | 클러스터 종료 | 다중 커널 세션 | 모든 커널 종료 |
| TS-006 | 이미 종료됨 | 커널 이미 TERMINATED | skipped |

#### 1.5 DeprioritizeSessionsLifecycleHandler

**목적**: 재시도 초과 세션 우선순위 하락 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| DP-001 | 우선순위 하락 | DEPRIORITIZING 세션 | PENDING으로 전환, 낮은 priority |
| DP-002 | 이미 최저 우선순위 | priority=0 | CANCELLED 전환 |
| DP-003 | 빈 입력 | 세션 없음 | 빈 결과 |

#### 1.6 SweepSessionsLifecycleHandler

**목적**: 고아 상태 세션 정리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| SW-001 | Stale PREPARING | PREPARING 상태 > timeout | TERMINATING 전환 |
| SW-002 | Stale PULLING | PULLING 상태 > timeout | TERMINATING 전환 |
| SW-003 | 정상 세션 | timeout 미초과 | skipped |
| SW-004 | 커널 없는 세션 | 세션만 존재, 커널 0개 | CANCELLED 전환 |

---

### 2. Scheduler Promotion Handlers

#### 2.1 PromoteToPreparedPromotionHandler

**목적**: 이미지 풀링 완료 확인 및 PREPARED 승격

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| PP-001 | 풀링 완료 | 모든 커널 이미지 ready | successes, PREPARED 전환 |
| PP-002 | 풀링 진행중 | 일부 커널 풀링중 | skipped |
| PP-003 | 풀링 실패 | 에이전트에서 에러 | failures |
| PP-004 | 클러스터 풀링 | 다중 커널 세션 | 모든 커널 완료 시 승격 |
| PP-005 | Timeout 초과 | PULLING > 15분 | failures (expired) |

#### 2.2 PromoteToRunningPromotionHandler

**목적**: 컨테이너 생성 완료 확인 및 RUNNING 승격

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| PR-001 | 생성 완료 | 모든 커널 container_id 존재 | successes, RUNNING 전환 |
| PR-002 | 생성 진행중 | container_id=None | skipped |
| PR-003 | 생성 실패 | 에이전트 에러 | failures |
| PR-004 | 클러스터 생성 | 다중 커널 | 모든 커널 완료 시 승격 |
| PR-005 | Timeout 초과 | CREATING > 10분 | failures (expired) |
| PR-006 | 부분 실패 | 일부 커널만 생성됨 | failures (전체 세션) |

#### 2.3 DetectTerminationPromotionHandler

**목적**: TERMINATING 세션의 커널 종료 상태 감지

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| DT-001 | 모든 커널 종료됨 | 모든 커널 TERMINATED | successes |
| DT-002 | 종료 진행중 | 일부 커널 TERMINATING | skipped |
| DT-003 | 에이전트 LOST | 에이전트 연결 불가 | successes (강제 완료) |
| DT-004 | 혼합 상태 | 일부 TERMINATED, 일부 RUNNING | skipped |

#### 2.4 PromoteToTerminatedPromotionHandler

**목적**: 세션을 TERMINATED 최종 상태로 전환

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| PT-001 | 정상 종료 | TERMINATING 세션 | TERMINATED, result 기록 |
| PT-002 | 에러로 종료 | status_info="error" | TERMINATED, result=ERROR |
| PT-003 | 사용자 취소 | status_info="user-requested" | TERMINATED, result=USER_CANCELLED |

---

### 3. Scheduler Kernel Handlers

#### 3.1 SweepStaleKernelsKernelHandler

**목적**: RUNNING 커널 중 stale 상태 감지 및 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| SK-001 | Stale 커널 감지 | last_stat > threshold | 커널 TERMINATING 전환 |
| SK-002 | 정상 커널 | last_stat 최신 | 변경 없음 |
| SK-003 | 에이전트 LOST | 에이전트 연결 불가 | 커널 TERMINATING 전환 |
| SK-004 | 컨테이너 없음 | container_id=None, RUNNING | 커널 TERMINATED 전환 |

---

### 4. Deployment Handlers

#### 4.1 CheckPendingDeploymentHandler

**목적**: PENDING 디플로이먼트 처리 및 초기 세션 생성

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| CD-001 | 신규 디플로이먼트 | PENDING 상태 | PROVISIONING 전환, 세션 생성 요청 |
| CD-002 | 리소스 부족 | 가용 리소스 없음 | PENDING 유지, 재시도 대기 |
| CD-003 | 설정 오류 | 잘못된 이미지 | FAILED 전환 |

#### 4.2 CheckReplicaDeploymentHandler

**목적**: 레플리카 수 유지 확인

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| CR-001 | 레플리카 정상 | current == desired | 변경 없음 |
| CR-002 | 레플리카 부족 | current < desired | 스케일업 트리거 |
| CR-003 | 레플리카 초과 | current > desired | 스케일다운 트리거 |
| CR-004 | 비정상 레플리카 | unhealthy 레플리카 존재 | 교체 트리거 |

#### 4.3 ScalingDeploymentHandler

**목적**: 디플로이먼트 스케일 업/다운 실행

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| SC-001 | 스케일 업 | desired_replicas 증가 | 새 세션 생성 |
| SC-002 | 스케일 다운 | desired_replicas 감소 | 세션 종료 (우선순위 낮은 것부터) |
| SC-003 | 점진적 스케일 | 대량 변경 | 배치 처리 |
| SC-004 | 리소스 부족 시 스케일업 | 가용 리소스 없음 | 부분 스케일업, 나머지 대기 |

#### 4.4 ReconcileDeploymentHandler

**목적**: 상태 불일치 조정

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RC-001 | 세션 상태 불일치 | DB와 실제 상태 다름 | 상태 동기화 |
| RC-002 | 고아 세션 | 디플로이먼트 없는 세션 | 세션 종료 |
| RC-003 | 라우트 불일치 | 라우트 없는 레플리카 | 라우트 생성 |

#### 4.5 DestroyingDeploymentHandler

**목적**: 디플로이먼트 삭제 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| DD-001 | 정상 삭제 | DESTROYING 디플로이먼트 | 모든 세션 종료, DESTROYED 전환 |
| DD-002 | 세션 종료 중 | 일부 세션 TERMINATING | DESTROYING 유지, 대기 |
| DD-003 | 강제 삭제 | force=True | 즉시 DESTROYED, 비동기 정리 |

---

### 5. Route Handlers

#### 5.1 ProvisioningRouteHandler

**목적**: 라우트 초기 프로비저닝

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RP-001 | 정상 프로비저닝 | PROVISIONING 라우트 | 세션 연결, HEALTH_CHECKING 전환 |
| RP-002 | 세션 미준비 | 세션 아직 PREPARING | PROVISIONING 유지 |
| RP-003 | 세션 실패 | 세션 TERMINATED | FAILED 전환 |

#### 5.2 HealthCheckRouteHandler

**목적**: 라우트 헬스체크 수행

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RH-001 | 헬스체크 성공 | 엔드포인트 응답 정상 | RUNNING 전환 |
| RH-002 | 헬스체크 실패 | 엔드포인트 무응답 | 재시도 후 FAILED |
| RH-003 | 타임아웃 | 응답 지연 | 재시도 |
| RH-004 | 연속 성공 필요 | success_threshold=3 | 3회 연속 성공 시 전환 |

#### 5.3 RunningRouteHandler

**목적**: 실행 중 라우트 모니터링

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RR-001 | 정상 상태 | 헬스체크 통과 | RUNNING 유지 |
| RR-002 | 헬스체크 실패 | 연속 실패 | UNHEALTHY 전환 |
| RR-003 | 세션 종료 | 연결된 세션 TERMINATED | TERMINATING 전환 |
| RR-004 | 트래픽 분산 | weight 업데이트 | 라우팅 테이블 갱신 |

#### 5.4 RouteEvictionRouteHandler

**목적**: 비정상 라우트 퇴출

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RE-001 | 퇴출 실행 | UNHEALTHY 라우트 | EVICTING 전환, 트래픽 차단 |
| RE-002 | 대체 라우트 존재 | 다른 healthy 라우트 있음 | 트래픽 재분배 |
| RE-003 | 마지막 라우트 | 대체 불가 | 경고 발생, 서비스 다운 알림 |

#### 5.5 TerminatingRouteHandler

**목적**: 라우트 종료 처리

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| RT-001 | 정상 종료 | TERMINATING 라우트 | TERMINATED 전환 |
| RT-002 | 연결 드레인 | 활성 연결 존재 | 드레인 완료 대기 |
| RT-003 | 강제 종료 | timeout 초과 | 즉시 TERMINATED |

#### 5.6 ServiceDiscoverySyncRouteHandler

**목적**: 서비스 디스커버리 동기화

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| SD-001 | 라우트 등록 | 새 RUNNING 라우트 | 디스커버리에 등록 |
| SD-002 | 라우트 해제 | TERMINATED 라우트 | 디스커버리에서 제거 |
| SD-003 | 메타데이터 업데이트 | weight 변경 | 디스커버리 메타데이터 갱신 |
| SD-004 | 동기화 실패 | 디스커버리 연결 실패 | 재시도 큐잉 |

---

### 6. Coordinator Integration Tests

#### 6.1 Failure Classification

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| FC-001 | Need Retry | 첫 실패, timeout 미초과 | retry transition 적용 |
| FC-002 | Expired | timeout 초과 | expired transition 적용 |
| FC-003 | Give Up | max_retries 초과 | give_up transition 적용 |

#### 6.2 Hook Execution

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| HE-001 | Running Hook | RUNNING 전환 성공 | occupied_slots 업데이트, 이벤트 발행 |
| HE-002 | Terminated Hook | TERMINATED 전환 성공 | 리소스 해제, 이벤트 발행 |
| HE-003 | Hook 실패 | Hook 실행 중 예외 | 로그 기록, 전환은 완료 |

#### 6.3 Distributed Lock

| ID | 시나리오 | 입력 | 기대 결과 |
|----|----------|------|-----------|
| DL-001 | Lock 획득 | 첫 번째 요청 | 핸들러 실행 |
| DL-002 | Lock 경쟁 | 동시 요청 | 하나만 실행, 나머지 대기 |
| DL-003 | Lock 타임아웃 | 장시간 대기 | 타임아웃 후 다음 주기에 재시도 |

---

## Migration / Compatibility

### Backward Compatibility
- 기존 테스트는 유지하되, 새 패턴으로 점진적 이관
- Mock 기반 단위 테스트와 실제 DB 기반 통합 테스트 병행

### Breaking Changes
- 없음 (테스트 코드 추가만)

## Implementation Plan

### Phase 1: 테스트 인프라 구축
1. 테스트 디렉토리 구조 생성
2. 공통 fixture 정의 (mock repository, mock launcher 등)
3. 테스트 데이터 팩토리 생성

### Phase 2: Scheduler Handler 테스트
1. Lifecycle Handler 테스트 (6개)
2. Promotion Handler 테스트 (4개)
3. Kernel Handler 테스트 (1개)
4. Coordinator 통합 테스트

### Phase 3: Deployment Handler 테스트
1. Deployment Handler 테스트 (5개)
2. Route Handler 테스트 (6개)

### Phase 4: E2E 시나리오 테스트
1. 세션 전체 생명주기 테스트
2. 디플로이먼트 스케일링 시나리오
3. 장애 복구 시나리오

## Open Questions

1. Mock vs Real DB 비율은 어떻게 가져갈 것인가?
   - 단위 테스트: Mock 기반
   - 통합 테스트: Real DB (PostgreSQL testcontainer)
==> repository 테스트와 component test 에서만 Real DB 를 사용할 생각

2. 외부 의존성(에이전트 RPC) 테스트 방법?
   - Mock agent client 사용
   - 필요시 integration 테스트에서 실제 에이전트 사용

3. 비동기 이벤트 검증 방법?
   - EventProducer mock으로 발행 이벤트 capture
   - assertion으로 이벤트 내용 검증

## References

- [BEP-1029: Sokovan Observer Handler](BEP-1029-sokovan-observer-handler.md)
- [BEP-1030: Sokovan Scheduler Status Transition](BEP-1030-sokovan-scheduler-status-transition.md)
- [BA-3936: Scheduling Coordinator Integration](https://lablup.atlassian.net/browse/BA-3936)
