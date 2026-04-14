# Model Deployment 무중단 배포 — 백엔드 진행 상황 공유

## 1. 현재 상태

BEP-1049 기반 무중단 배포(Zero-Downtime Deployment) 백엔드 구현이 완료되었습니다.

| 기능 | 상태 |
|------|------|
| Rolling Update | 구현 완료, E2E 테스트 통과, 머지됨 |
| Blue-Green (auto_promote) | 구현 완료, 테스트 중 |
| Blue-Green (manual_promote) | 구현 완료, 테스트 중 |
| Rollback (timeout 기반) | 구현 완료 |

> 데모 로그, GIF, 스크린샷 등은 여기에 첨부 예정

---

## 2. 동작 방식 (BEP-1049)

### 2-1. Rolling Update

기존 라우트(Old Revision)를 새 라우트(New Revision)로 점진적으로 교체하는 전략입니다.

**설정 파라미터:**

| 파라미터 | 설명 | 기본값 |
|----------|------|--------|
| `max_surge` | `desired_replicas`를 초과하여 동시에 생성할 수 있는 최대 추가 라우트 수 | `1` |
| `max_unavailable` | `desired_replicas` 대비 허용되는 최대 비가용 라우트 수 | `0` |

**동작 흐름 예시** (`desired=3`, `max_surge=1`, `max_unavailable=1`):

```
Cycle 0: Old [■ ■ ■]                 → New 1개 생성, Old 1개 종료
Cycle 1: Old [■ ■], New [◇]          → 프로비저닝 대기
Cycle 2: Old [■ ■], New [■]          → New 1개 추가 생성, Old 1개 추가 종료
Cycle 3: Old [■], New [■ ◇]          → 프로비저닝 대기
Cycle 4: Old [■], New [■ ■]          → New 1개 추가 생성, Old 1개 추가 종료
Cycle 5: Old [], New [■ ■ ◇]         → 프로비저닝 대기
Cycle 6: Old [], New [■ ■ ■]         → 완료! deploying_revision → current_revision 스왑

■ = healthy, ◇ = provisioning
```

**핵심 특징:**
- 새 라우트는 생성 즉시 ACTIVE 상태로 트래픽을 수신
- Old/New 라우트가 공존하면서 점진적으로 교체
- `max_surge`와 `max_unavailable`로 교체 속도와 안정성 간 균형 조절

---

### 2-2. Blue-Green Update

기존 라우트(Blue)를 유지하면서 새 라우트(Green)를 전부 생성한 뒤, 모두 healthy가 되면 트래픽을 한번에 전환하는 전략입니다.

**설정 파라미터:**

| 파라미터 | 설명 | 기본값 |
|----------|------|--------|
| `auto_promote` | Green이 모두 healthy가 되면 자동으로 트래픽을 전환할지 여부 | `false` |
| `promote_delay_seconds` | 자동 전환 전 대기 시간 (초) | `0` |

**동작 흐름 예시** (`desired=3`, `auto_promote=true`, `delay=0`):

```
Cycle 0: Blue [■ ■ ■ ACTIVE]                          → Green 3개 생성 (INACTIVE)
Cycle 1: Blue [■ ■ ■ ACTIVE], Green [◇ ◇ ◇ INACTIVE]  → 프로비저닝 대기
Cycle 2: Blue [■ ■ ■ ACTIVE], Green [■ ◇ ◇ INACTIVE]  → 프로비저닝 대기
Cycle 3: Blue [■ ■ ■ ACTIVE], Green [■ ■ ■ INACTIVE]  → 전체 healthy!
         → Green: INACTIVE → ACTIVE (트래픽 전환)
         → Blue: ACTIVE → TERMINATING (종료)
         → 완료! deploying_revision → current_revision 스왑

■ = healthy, ◇ = provisioning
```

**핵심 특징:**
- Green 라우트는 INACTIVE 상태로 생성되어 promotion 전까지 트래픽을 받지 않음
- 트래픽 전환이 atomic (Blue → Green 한번에 전환)
- `auto_promote=false`인 경우, Green이 모두 healthy가 되어도 수동 promotion API 호출 전까지 대기
- 롤백이 간단: Green만 종료하면 됨 (Blue가 그대로 살아있으므로)

---

### 2-3. Rolling Update vs Blue-Green 비교

| 항목 | Rolling Update | Blue-Green |
|------|---------------|------------|
| 라우트 생성 | 점진적 (`max_surge` 제어) | 한번에 전부 |
| 새 라우트 트래픽 | 즉시 ACTIVE | INACTIVE (promotion 전까지) |
| 기존 라우트 제거 | 점진적 (`max_unavailable` 제어) | promotion 시 한번에 |
| 트래픽 전환 | 점진적 (생성/제거와 동시) | Atomic (한번에 전환) |
| 리소스 사용 | `max_surge`만큼 추가 | 전환 시점에 2배 리소스 |
| 롤백 | 부분 교체 상태에서 복구 필요 | Green 종료만 하면 됨 (Blue 유지) |

---

### 2-4. Rollback

두 전략 모두 30분 timeout 기반 자동 롤백을 지원합니다.

- 새 라우트가 timeout 내에 healthy 상태에 도달하지 못하면, coordinator가 deployment를 `ROLLING_BACK` 상태로 전환
- `deploying_revision`을 `NULL`로 설정하고, 기존 `current_revision`을 유지한 채 `READY` 상태로 복귀

---

## 3. 새로 추가/변경된 GraphQL API

### Mutations

| Mutation | 설명 |
|----------|------|
| `createModelDeployment(input)` | 새 디플로이먼트(엔드포인트) 생성. `default_deployment_strategy`로 초기 전략 설정 가능 |
| `updateModelDeployment(input)` | 디플로이먼트 설정 업데이트 |
| `deleteModelDeployment(input)` | 디플로이먼트 삭제 |
| `updateDeploymentPolicy(input)` | 디플로이먼트 정책 생성/수정 (upsert). Rolling/Blue-Green 전략 설정 **(신규)** |
| `addModelRevision(input)` | 디플로이먼트에 새 리비전 추가 |
| `activateDeploymentRevision(input)` | 리비전 활성화. policy 존재 시 무중단 배포 시작 **(신규)** |

### Queries

| Query | 설명 |
|-------|------|
| `deployments(filter, orderBy, ...)` | 디플로이먼트 검색 (페이지네이션) |
| `deployment(id)` | 특정 디플로이먼트 조회 |
| `revisions(filter, orderBy, ...)` | 리비전 검색 (페이지네이션) |
| `revision(id)` | 특정 리비전 조회 |

---

## 4. 클라이언트 플로우

```
① createModelDeployment
   └─ 새 디플로이먼트(엔드포인트) 생성
   └─ default_deployment_strategy로 초기 전략을 함께 설정 가능

② updateDeploymentPolicy  (①에서 policy를 함께 생성하지 않았다면)
   └─ 배포 전략 설정 (ROLLING / BLUE_GREEN + 상세 파라미터)

③ addModelRevision
   └─ 생성한 디플로이먼트에 새 리비전 추가
   └─ 리비전: 이미지, 리소스, 런타임 설정, 모델 마운트 등의 스냅샷

④ activateDeploymentRevision
   └─ 생성한 리비전을 활성화
   └─ policy 존재 시 → 무중단 배포 시작 (DEPLOYING 상태)
   └─ policy 미존재 시 → 즉시 리비전 스왑 (기존 동작)
```

---

## 5. 프론트엔드 대응 필요 사항

### 5-1. Deployment Policy

- **서비스 정보 페이지**: deployment policy를 보여주는 UI 추가
  - 현재 설정된 전략 타입 (Rolling / Blue-Green)
  - 전략별 상세 파라미터 (`max_surge`, `max_unavailable` / `auto_promote`, `promote_delay_seconds`)
- **서비스 수정 페이지**: deployment policy를 업데이트할 수 있는 UI 추가
  - 전략 타입 선택 드롭다운
  - 전략별 파라미터 입력 폼

### 5-2. Deployment Revision

- **리비전 리스트**: 리비전 목록을 볼 수 있는 페이지/UI
  - 라우팅 정보 페이지에 리비전 테이블 삽입 형태 등
  - 페이지네이션 지원 (cursor / offset)
  - 필터/정렬 지원 (`name`, `created_at`)
- **리비전 추가**: "리비전 추가" 버튼 → 모달 창
  - 입력 항목: `name`, `cluster_config`, `resource_config`, `image`, `model_runtime_config`, `model_mount_config`, `extra_mounts`
  - 생성하기 클릭 → `addModelRevision` mutation 호출
- **리비전 상세 / 활성화**: 리비전 클릭 → 리비전 정보 모달
  - 현재 리비전과 해당 리비전 값이 다르고, deployment policy가 존재하는 경우 "적용하기" 버튼 활성화
  - "적용하기" 클릭 → `activateDeploymentRevision` mutation 호출 → 무중단 배포 시작

### 5-3. Deployment History

- 라우팅 정보 페이지에 테이블 형태로 넣는 것이 적합할지 검토 필요
- 필요하다면 히스토리 테이블 추가 가능

---

## 6. 참고 자료

- [BEP-1049: Zero-Downtime Deployment Strategy Architecture](https://github.com/lablup/backend.ai/blob/main/proposals/BEP-1049-deployment-strategy-handler.md)
  - [Rolling Update](https://github.com/lablup/backend.ai/blob/main/proposals/BEP-1049/rolling-update.md)
  - [Blue-Green](https://github.com/lablup/backend.ai/blob/main/proposals/BEP-1049/blue-green.md)
- **BEP-1006**: Service Deployment Strategy (상위 BEP)

---

## 7. Rolling Update E2E 실행 로그 (replica=3, maxSurge=1, maxUnavailable=0)

> 2026-03-24 개발 환경(bndev)에서 실행한 실제 E2E 결과입니다.
> 이미지: `cr.backend.ai/stable/python:3.10-ubuntu22.04-amd64`, 리소스: CPU 1 / Mem 1GiB

### 7-1. 초기 Deployment 생성 (Step 1-2)

```
[Step 1] Creating deployment with 3 replicas (Rolling strategy)
  Deployment ID: 15254e68-a72b-4847-b55c-a20519eb523e
  Status: PENDING → SCALING → READY
  Strategy: ROLLING (maxSurge=1, maxUnavailable=0)
```

**Manager 로그 (Deployment 등록 ~ Route 프로비저닝):**

```
14:51:21.668  Creating deployment with name: rolling-e2e-1774331481
14:51:22.749  handler: check-pending-deployments - processing 1 deployments
14:51:22.795  Successfully registered endpoint for deployment 15254e68 with URL: http://192.168.0.18:10272/
14:51:22.807  Marked deployment lifecycle needed for type: scaling
14:51:23.610  Scaled 1 deployments
14:51:24.836  Provisioning 3 routes
14:51:24.905  Session rolling-e2e-...-f66613c0 (8234b148) enqueued successfully
14:51:24.950  Session rolling-e2e-...-56abc6f5 (7e386dc0) enqueued successfully
14:51:24.994  Session rolling-e2e-...-b21a4208 (080b7005) enqueued successfully
14:51:25.007  Provisioned 3 routes successfully, 0 failed
```

**Route 상태 변화:**

```
[  0s] PENDING        → Routes: 0
[  3s] READY          → Routes: 3 × PROVISIONING (세션 미할당)
[  6s] READY          → Routes: 3 × DEGRADED (세션 할당됨, health check 대기)
[ 83s] READY          → Routes: 3 × HEALTHY ← v1 배포 완료!
```

**Manager 로그 (Health Check):**

```
14:52:03  Health check: 0 healthy, 0 unhealthy, 3 degraded
14:52:44  Health check: 3 healthy, 0 unhealthy, 0 degraded    ← ~80초 후 HEALTHY
```

---

### 7-2. Revision v2 추가 & 활성화 (Step 3-4)

```
[Step 3] Adding new revision v2
  New Revision ID: fb01cb06-4d4d-476f-9287-fdef11a80705

[Step 4] Activating revision v2 (triggers Rolling Update)
  Deployment Status: DEPLOYING
  DB: lifecycle=deploying, sub_step=deploying_provisioning
```

**Manager 로그:**

```
14:52:45.101  Adding model revision to deployment 15254e68
14:52:45.144  Started deploying revision fb01cb06 for deployment 15254e68 (current: None)
14:52:45.144  Marked deployment lifecycle needed for type: deploying, sub_step: deploying_provisioning
```

---

### 7-3. Rolling Update Cycle 상세 (Step 5)

> `■` = HEALTHY, `◇` = PROVISIONING, `△` = DEGRADED, `×` = TERMINATING/TERMINATED

#### Cycle 0 [0s] — 초기 상태, New route 1개 생성

```
  Old (v1): [■ ■ ■]  (HEALTHY=3)
  New (v2): []
```

**Manager 로그 (Strategy FSM 평가):**

```
14:52:49  deployment 15254e68: sub_step=deploying_provisioning,
          routes total=3, old_active=3, new_prov=0, new_healthy=0
14:52:49  PROVISIONING create=1, terminate=0, old_active=3, new_healthy=0
          → surge 예산: max_total(3+1=4) - current(3) = 1개 생성 가능
          → 종료 예산: available(3) - min_available(3-0=3) = 0개 종료 가능
14:52:49  Applied evaluation: 1 routes created, 0 routes drained
```

#### Cycle 1 [6s] — New route PROVISIONING (세션 생성 중)

```
  Old (v1): [■ ■ ■]  (HEALTHY=3)
  New (v2): [◇]      (PROVISIONING=1)
```

**Manager 로그:**

```
14:52:53  Provisioning 1 routes
14:52:53  1 new routes still provisioning    ← FSM이 대기 결정
```

#### Cycle 2 [9s] — New route DEGRADED (health check 대기)

```
  Old (v1): [■ ■ ■]  (HEALTHY=3)
  New (v2): [△]      (DEGRADED=1)
```

**Manager 로그:**

```
14:53:03  Health check: 3 healthy, 0 unhealthy, 1 degraded
14:53:04  1 new routes still provisioning    ← DEGRADED도 is_provisioning()=True
```

> **참고**: `DEGRADED` 상태는 컨테이너는 실행 중이나 health check가 아직 통과하지 못한 상태.
> Strategy FSM에서는 `is_provisioning()=True`로 분류되어, HEALTHY가 될 때까지 대기합니다.

#### Cycle 3 [92s] — New 첫 번째 HEALTHY! Old 1개 drain 시작

```
  Old (v1): [■ ■ ×]  (HEALTHY=2, TERMINATING=1)
  New (v2): [■]      (HEALTHY=1)
```

**Manager 로그:**

```
14:54:14  Health check: 4 healthy, 0 unhealthy, 0 degraded    ← New route HEALTHY 전환
14:54:14  deployment 15254e68: old_active=3, new_prov=0, new_healthy=1
14:54:14  PROVISIONING create=0, terminate=1, old_active=3, new_healthy=1
          → surge 예산: max_total(4) - current(4) = 0개 생성 가능
          → 종료 예산: available(3+1=4) - min_available(3) = 1개 종료 가능
14:54:14  Applied evaluation: 0 routes created, 1 routes drained
14:54:31  notified app proxy of route removal for endpoint 15254e68 (session 8234b148)
```

#### Cycle 4 [95s] — Old drain 확인, New 2번째 생성

```
  Old (v1): [■ ■ ×]  (HEALTHY=2, TERMINATING=1)
  New (v2): [◇ ■]    (HEALTHY=1, PROVISIONING=1)
```

**Manager 로그:**

```
14:54:19  deployment 15254e68: old_active=2, new_healthy=1
14:54:19  PROVISIONING create=1, terminate=0, old_active=2, new_healthy=1
          → surge 예산: max_total(4) - current(3) = 1개 생성 가능
          → 종료 예산: available(2+1=3) - min_available(3) = 0개 종료 가능
14:54:19  Applied evaluation: 1 routes created, 0 routes drained
14:54:24  Provisioning 1 routes
```

#### Cycle 5-6 [101-105s] — New 2번째 DEGRADED → health check 대기

```
  Cycle 5: Old [■ ■ ×], New [△ ■]  (DEGRADED=1, HEALTHY=1)
  Cycle 6: Old [■ ■ ×], New [△ ■]  (Old 1개 TERMINATED)
```

**Manager 로그:**

```
14:55:03  Health check: 3 healthy, 0 unhealthy, 1 degraded
          → 1 new routes still provisioning
```

#### Cycle 7 [182s] — New 2번째 HEALTHY! Old 2번째 drain

```
  Old (v1): [■ ■ ×]  (HEALTHY=2, TERMINATED=1)
  New (v2): [■ ■]    (HEALTHY=2)
```

**Manager 로그:**

```
14:55:49  deployment 15254e68: old_active=2, new_healthy=2
14:55:49  PROVISIONING create=0, terminate=1, old_active=2, new_healthy=2
          → 종료 예산: available(2+2=4) - min_available(3) = 1개 종료 가능
14:55:49  Applied evaluation: 0 routes created, 1 routes drained
14:56:01  notified app proxy of route removal for endpoint 15254e68 (session 7e386dc0)
```

#### Cycle 8 [185s] — Old drain 확인, New 3번째 생성

```
  Old (v1): [× ■ ×]  (HEALTHY=1, TERMINATED=1, TERMINATING=1)
  New (v2): [■ ■]    (HEALTHY=2)
```

**Manager 로그:**

```
14:55:53  PROVISIONING create=1, terminate=0, old_active=1, new_healthy=2
          → surge 예산: max_total(4) - current(3) = 1개 생성 가능
14:55:53  Applied evaluation: 1 routes created, 0 routes drained
```

#### Cycle 9-11 [188-194s] — New 3번째 PROVISIONING → DEGRADED → health check 대기

```
  Cycle  9: Old [× ■ ×], New [◇ ■ ■]  (PROVISIONING=1, HEALTHY=2)
  Cycle 10: Old [× ■ ×], New [△ ■ ■]  (DEGRADED=1, HEALTHY=2)
  Cycle 11: Old [× ■ ×], New [△ ■ ■]  (Old 2번째 TERMINATED)
```

#### Cycle 12 [272s] — New 3번째 HEALTHY! Old 마지막 drain, 완료 직전

```
  Old (v1): [× × ×]  (TERMINATED=2, TERMINATING=1)
  New (v2): [■ ■ ■]  (HEALTHY=3)
```

**Manager 로그:**

```
14:57:15  PROVISIONING create=0, terminate=1, old_active=1, new_healthy=3
          → 종료 예산: available(1+3=4) - min_available(3) = 1개 종료 가능
14:57:15  Applied evaluation: 0 routes created, 1 routes drained
```

#### Cycle 13 [275s] — Rolling Update 완료! Revision Swap!

```
  Old (v1): [× × ×]  (TERMINATED=3)
  New (v2): [■ ■ ■]  (HEALTHY=3)

  DB: lifecycle=ready, sub_step=None
  DB: current_revision=fb01cb06 (v2), deploying_revision=None
```

**Manager 로그:**

```
14:57:20  deployment 15254e68: rolling update complete (3 healthy routes)
          → sub_step = DEPLOYING_COMPLETED
14:57:20  Applied evaluation: 0 routes created, 0 routes drained
          → deploying_revision → current_revision 스왑 (atomic)
          → deploying_revision = NULL, sub_step = NULL
          → lifecycle_stage: deploying → ready
14:57:31  notified app proxy of route removal for endpoint 15254e68 (session 080b7005)
          → 마지막 Old route 정리 완료
```

---

### 7-4. 타임라인 요약

| 시간 | 이벤트 | Old Routes | New Routes |
|------|--------|-----------|-----------|
| 0s | Deployment 생성 (PENDING) | 0 | 0 |
| 3s | Route 3개 생성 (SCALING→READY) | 3×PROV | 0 |
| 6s | 세션 할당 (DEGRADED) | 3×DEG | 0 |
| 83s | v1 전체 HEALTHY | 3×**HEALTHY** | 0 |
| 83s | v2 리비전 추가 + 활성화 (DEPLOYING) | 3×HEALTHY | 0 |
| 86s | New #1 생성 (create=1) | 3×HEALTHY | 1×PROV |
| 89s | New #1 DEGRADED (health check 대기) | 3×HEALTHY | 1×DEG |
| 172s | New #1 **HEALTHY**, Old #1 drain | 2×HEALTHY + 1×TERM | 1×**HEALTHY** |
| 175s | New #2 생성 (create=1) | 2×HEALTHY + 1×TERM | 1×HEALTHY + 1×PROV |
| 181s | New #2 DEGRADED | 2×HEALTHY + 1×TERM | 1×HEALTHY + 1×DEG |
| 262s | New #2 **HEALTHY**, Old #2 drain | 1×HEALTHY + 2×TERM | 2×**HEALTHY** |
| 265s | New #3 생성 (create=1) | 1×HEALTHY + 2×TERM | 2×HEALTHY + 1×PROV |
| 268s | New #3 DEGRADED | 1×HEALTHY + 2×TERM | 2×HEALTHY + 1×DEG |
| 352s | New #3 **HEALTHY**, Old #3 drain | 3×TERM | 3×**HEALTHY** |
| 355s | **Rolling Update 완료!** Revision Swap | 0 (all terminated) | 3×HEALTHY |

**총 소요시간: ~275초 (4분 35초)**

> 대부분의 시간은 DEGRADED → HEALTHY 전환의 health check 대기 시간(~80초)입니다.
> Strategy FSM의 evaluate_cycle 자체는 밀리초 단위로 실행됩니다.

---

### 7-5. Strategy FSM 결정 로그 요약

각 cycle에서 FSM이 내린 결정을 정리한 표입니다.

| Cycle | old_active | new_prov | new_healthy | create | terminate | 설명 |
|-------|-----------|---------|------------|--------|-----------|------|
| 0 | 3 | 0 | 0 | **1** | 0 | surge 예산으로 New 1개 생성 |
| 1-2 | 3 | 1 | 0 | 0 | 0 | PROVISIONING/DEGRADED 대기 |
| 3 | 3 | 0 | **1** | 0 | **1** | New HEALTHY → Old 1개 drain |
| 4 | 2 | 0 | 1 | **1** | 0 | surge 여유로 New 2번째 생성 |
| 5-6 | 2 | 1 | 1 | 0 | 0 | PROVISIONING/DEGRADED 대기 |
| 7 | 2 | 0 | **2** | 0 | **1** | New HEALTHY → Old 2번째 drain |
| 8 | 1 | 0 | 2 | **1** | 0 | surge 여유로 New 3번째 생성 |
| 9-11 | 1 | 1 | 2 | 0 | 0 | PROVISIONING/DEGRADED 대기 |
| 12 | 1 | 0 | **3** | 0 | **1** | New HEALTHY → Old 마지막 drain |
| 13 | 0 | 0 | 3 | — | — | **COMPLETED** → revision swap |

---

## 8. 추가 작업 (TBD)

- (여기에 추가 작업 항목 기입)
