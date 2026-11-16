# Phase 2: 스케줄러 통합

> [BEP-1047](../BEP-1047-resource-slot-db-normalization.md) 의 상세 문서

새 테이블을 스케줄러 lifecycle 에 연결해 SQL 기반 점유량 계산을 가능하게 한다.

## 2.1 kernel lifecycle 통합

lifecycle 단계마다 자원 기록을 변경한다.

| 단계 | 현재 코드 | 변경 |
|-------|-------------|--------|
| 세션 생성 | `_allocate_single_session()` 이 `requested_slots` JSONB 를 기록한다 | `resource_allocations` 에도 INSERT 한다 |
| 실행 전이 | `_update_occupied_slots()` 가 `occupied_slots` JSONB 를 기록한다 | `resource_allocations.used` 도 UPDATE 한다 |
| 종료 | 상태 전이가 slot 을 삭제한다 | `resource_allocations` 에서 DELETE 한다 |

Phase 2 에서는 검증을 위해 JSONB 와 정규화 테이블 양쪽에 **dual-write** 한다.

## 2.2 점유량 계산 (SQL)

`_fetch_kernel_occupancy()` 의 Python 집계를 SQL 로 대체한다.

```sql
-- Build ResourceOccupancySnapshot via SQL
SELECT
    k.access_key,
    k.user_uuid,
    k.group_id,
    k.domain_name,
    k.agent,
    ra.slot_name,
    SUM(CASE
        WHEN k.status IN ('RUNNING', 'TERMINATING') THEN ra.used
        ELSE ra.requested
    END) AS amount
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.scaling_group = :scaling_group
  AND k.status = ANY(:resource_statuses)
GROUP BY k.access_key, k.user_uuid, k.group_id, k.domain_name, k.agent, ra.slot_name;
```

row 마다 수행하던 Python 역직렬화와 누적 반복을 제거한다.

## 2.3 validator 최적화

자원 한도 validator 는 현재 메모리의 `ResourceSlot` 객체를 비교한다.
정규화 테이블이 있으면 한도 검사를 SQL 로 옮길 수 있다.

```sql
-- Check if adding a workload exceeds domain limit
SELECT ra.slot_name,
       SUM(ra.used) AS current_usage
FROM resource_allocations ra
JOIN kernels k ON k.id = ra.kernel_id
WHERE k.domain_name = :domain_name
  AND k.status = ANY(:resource_statuses)
GROUP BY ra.slot_name;
```

정책 한도와의 비교는 Python 에 남고, 집계만 SQL 로 옮긴다.

## 2.4 영향받는 code 경로

| code 경로 | 파일 | 현재 동작 | Phase 2 이후 |
|-----------|------|-----------------|---------------|
| `_allocate_single_session()` | db_source.py | `requested_slots` JSONB INSERT | `resource_allocations` row 도 INSERT |
| `_update_occupied_slots()` | hooks/status.py | `occupied_slots` JSONB UPDATE | `resource_allocations.used` 도 UPDATE |
| `_fetch_kernel_occupancy()` | db_source.py | Python 반복 집계 | SQL GROUP BY 질의 |
| `_calculate_agent_occupied_slots()` | db_source.py | Python 반복 집계 | SQL GROUP BY 질의 |
| Domain/Group/Keypair/User validator | provisioner/validators/ | 메모리에서 ResourceSlot 비교 | SQL 집계 + Python 비교 |
