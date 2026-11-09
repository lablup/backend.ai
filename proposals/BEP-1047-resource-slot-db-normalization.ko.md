# Resource slot DB 정규화

## 관련 이슈

- JIRA Epic: [BA-4302](https://lablup.atlassian.net/browse/BA-4302) - Resource slot DB 정규화
- JIRA Stories:
  - [BA-4303](https://lablup.atlassian.net/browse/BA-4303) - Phase 1: 기반 테이블과 migration
- 관련 BEP:
  - [BEP-1026](BEP-1026-fair-share-scheduler.md) - Fair Share 스케줄러 (usage bucket / fair share 테이블)
  - [BEP-1000](BEP-1000-redefining-accelerator-metadata.md) - 가속기 메타데이터 재정의 (slot 메타데이터)

## 동기

Backend.AI 의 모든 resource slot 데이터는 `ResourceSlotColumn` 을 통해 **JSONB column** 으로 저장한다. 규모가 커지면 세 가지 중대한 문제가 생긴다.

1. **SQL 집계가 불가능하다**: 모든 집계가 모든 row 를 Python 메모리로 읽어 직접 반복해야 한다 (예: `_calculate_agent_occupied_slots()`, `_fetch_kernel_occupancy()`)
2. **원자 연산이 불가능하다**: 자원 하나를 변경하려면 JSONB 객체 전체를 읽고 변경하고 기록하는 방식이 필요해, 동시 스케줄링에서 race condition 이 생긴다
3. **엔티티 간 질의가 비효율적이다**: "project 별 총 GPU 사용량" 같은 질의에 `SELECT SUM(...) GROUP BY` 대신 전체 Python 스캔이 필요하다

Fair Share 스케줄러(BEP-1026)는 자원 × 엔티티 × bucket 일마다 Python `Decimal` 지수 계산을 적용해 이 문제를 키운다. 정규화 column 이 있으면 이것이 SQL window function 하나가 될 수 있다.

## 현재 설계

> 상세: [current-design.md](BEP-1047/current-design.md)

8개 테이블이 resource slot 을 JSONB 로 저장한다(`kernels`, `agents`, `*_usage_buckets`, `*_fair_shares`). slot 유형 정의는 etcd, `INTRINSIC_SLOTS`, `KNOWN_SLOT_METADATA`, `SlotTypes` enum 에 흩어져 있다.

모든 스케줄러 집계는 전체 결과 집합에 대한 Python 반복으로 이뤄진다.

## 제안 설계

JSONB resource slot 을 `(entity_id, slot_name, amount)` row 를 가진 관계형 테이블로 정규화해 SQL 기반 집계를 가능하게 하고, 단계별 migration 으로 하위 호환성을 유지한다.

### Phase 1: 기반 테이블 (비파괴)

> 상세: [phase-1-foundation-tables.md](BEP-1047/phase-1-foundation-tables.md)

기존 JSONB column 옆에 새 정규화 테이블을 추가한다. 기존 동작은 변경되지 않는다.

| 테이블 | 목적 | PK |
|-------|---------|-----|
| `resource_slot_types` | slot 유형 registry (etcd 와 hardcoded 정의를 대체) | `slot_name` |
| `agent_resources` | Agent 자원 목록 | `(agent_id, slot_name)` |
| `resource_allocations` | kernel 별 자원 할당 | `(kernel_id, slot_name)` |

주요 설계 결정: 복합 PK(UUID 없음), 모든 양에 `NUMERIC(24,6)`, `used` nullable(NULL 과 0 의 의미 구분), `ON DELETE CASCADE`.

### Phase 2: 스케줄러 통합

> 상세: [phase-2-scheduler-integration.md](BEP-1047/phase-2-scheduler-integration.md)

새 테이블을 kernel lifecycle(생성 → 실행 → 종료)에 dual-write 로 연결한다. Python 집계 반복을 SQL `GROUP BY` 질의로 대체한다. background task 로 JSONB 와 정규화 데이터를 검증한 뒤 전환한다.

### Phase 3: usage bucket 최적화

> 상세: [phase-3-usage-bucket-optimization.md](BEP-1047/phase-3-usage-bucket-optimization.md)

검토 중인 두 가지 접근 방식:
- **Option A**: JSONB SQL 집계 함수 (schema 변경 없음, 효율이 낮음)
- **Option B**: amount 와 duration 을 분리한 정규화 테이블 (overflow 위험 제거, Phase 1/2 와 일관됨)

Option B 는 미리 곱한 resource-seconds 대신 amount 와 duration 을 분리해 저장해, 저장하는 모든 값을 NUMERIC(24,6) 범위 안에 두고 곱셈을 SQL 질의 시점으로 미룬다.

## Migration / 호환성

> 상세: [migration-compatibility.md](BEP-1047/migration-compatibility.md)

| 단계 | 전략 | 위험 |
|-------|----------|------|
| Phase 1 | `CREATE TABLE` 만 하고 JSONB 에서 backfill | 없음. 비파괴 |
| Phase 2 | dual-write → 검증 → 전환 | 낮음. dual-write 를 비활성화하면 rollback |
| Phase 3 | JSONB deprecation → 제거 | 중간. 조율된 migration 필요 |

etcd slot 유형 정의는 점진적으로 옮긴다. DB 우선(Phase 1) → CLI import(Phase 2) → etcd 의존성 제거(Phase 3).

## 구현 계획

### Phase 1: 기반 (대상: BA-4303)

1. Alembic migration: 새 테이블 3개 생성
2. `INTRINSIC_SLOTS` + `KNOWN_SLOT_METADATA` 에서 `resource_slot_types` seed
3. 기존 JSONB 에서 `agent_resources` 와 `resource_allocations` backfill
4. row 모델과 repository 계층
5. 테스트: schema 검증, backfill 정확성, SQL 집계

### Phase 2: 스케줄러 통합

1. lifecycle 단계별 dual-write hook
2. SQL 집계 service (`_fetch_kernel_occupancy()`, `_calculate_agent_occupied_slots()` 대체)
3. background 검증 task
4. SQL 읽기 경로로 전환
5. 테스트: dual-write 일관성, SQL 과 Python 동등성

### Phase 3: usage bucket 최적화

1. 접근 방식 결정 (Option A 와 B 중 선택)
2. Python decay 계산을 SQL 로 대체해 구현
3. 성능 벤치마킹
4. 테스트: decay 정밀도 검증

## 열린 질문

1. **Phase 3 접근 방식**: JSONB SQL 함수(Option A)와 amount/duration 을 분리한 정규화 테이블(Option B) 중 선택
2. **Fair share decay 정밀도**: PostgreSQL `POWER()` 는 float64 를 사용한다. 현재 Python `Decimal` 과 비교해 충분한지 여부
3. **AcceleratorMetadata 통합**: `resource_slot_types` 가 BEP-1000 의 전체 schema 를 흡수하는 방향과 FK 로 분리해 두는 방향 중 선택
4. **etcd 에서 DB 로 옮기는 migration CLI**: 일회성 CLI 명령과 자동 alembic migration 중 선택
5. **index 전략**: 부분 index(예: `WHERE status IN ('RUNNING', 'TERMINATING')`) 추가 여부

## 참고

- [BEP-1026: Fair Share 스케줄러](BEP-1026-fair-share-scheduler.md) - usage bucket 과 fair share 테이블
- [BEP-1000: 가속기 메타데이터 재정의](BEP-1000-redefining-accelerator-metadata.md) - slot 메타데이터 설계
- [PostgreSQL JSONB 문서](https://www.postgresql.org/docs/16/datatype-json.html)
- [PostgreSQL Numeric 타입](https://www.postgresql.org/docs/16/datatype-numeric.html)
