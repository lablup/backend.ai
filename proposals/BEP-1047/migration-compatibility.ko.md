# Migration / 호환성

> [BEP-1047](../BEP-1047-resource-slot-db-normalization.md) 의 상세 문서

## Phase 1: 비파괴 추가

- **Schema** - `CREATE TABLE` 만 한다. 기존 테이블은 변경하지 않는다
- **데이터** - `INTRINSIC_SLOTS` 와 `KNOWN_SLOT_METADATA` 를 `resource_slot_types` 에 미리 저장한다
- **Backfill** - `agents.available_slots` / `agents.occupied_slots` 에서 `agent_resources` 채우기
- **Backfill** - `kernels.requested_slots` / `kernels.occupied_slots` 에서 `resource_allocations` 채우기
- **위험** - 없음. 기존 코드 경로에 영향이 없다

## Phase 2: 검증을 동반한 dual-write

- **기록 경로** - JSONB column 과 정규화 테이블 양쪽에 기록한다
- **읽기 경로** - 계속 JSONB(주 경로)에서 읽고, 정규화 테이블을 기준으로 검증한다
- **검증** - background task 가 JSONB 와 정규화 데이터를 비교하고 불일치를 log 로 남긴다
- **전환** - 검증이 일관되게 통과하면 읽기 경로를 정규화 테이블로 전환한다
- **Rollback** - dual-write 를 제거한다. 정규화 테이블은 오래된 상태가 되지만 다시 채울 수 있다

## Phase 3: JSONB column deprecation (향후)

- **Phase 2 안정화 후** - JSONB column 기록을 멈춘다
- **Migration** - JSONB column 을 deprecated 로 표시한다
- **제거** - 이후 major version 에서 alembic migration 과 함께 JSONB column 을 삭제한다

## 호환성을 깨는 변경

- **Phase 1** - 없음
- **Phase 2** - 스케줄러 데이터 소스의 내부 API 를 변경한다. 외부 API 에는 영향이 없다
- **Phase 3** - JSONB column 제거. JSONB 를 직접 질의하던 코드는 마이그레이션해야 한다

## etcd migration

현재 etcd(`config/resource_slots/{name}`)에 있는 resource slot 유형 정의에는 마이그레이션 경로가 필요하다.

1. **Phase 1** - etcd 와 `resource_slot_types` 테이블 양쪽에서 읽고, DB 를 우선한다
2. **Phase 2** - etcd slot 정의를 DB 로 가져오는 CLI 명령
3. **Phase 3** - slot 유형 registry 에서 etcd 의존성 제거
