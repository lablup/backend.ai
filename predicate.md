# Predicate 함수 데이터베이스 쿼리 분석

## 1. check_reserved_batch_session
**목적**: 배치 타입 세션이 예약된 시작 시간 이전에 시작되지 않도록 확인

**데이터베이스 쿼리**:
- `SessionRow.starts_at` where `SessionRow.id == sess_ctx.id`

**필요한 데이터**:
- 세션의 `starts_at` 타임스탬프
- 현재 세션의 `session_type` (sess_ctx에서)
- 현재 세션의 `id` (sess_ctx에서)

## 2. check_concurrency
**목적**: 사용자가 최대 동시 세션 제한에 도달했는지 확인

**데이터베이스 쿼리**:
1. `KeyPairRow.resource_policy` where `KeyPairRow.access_key == sess_ctx.access_key`
2. `KeyPairResourcePolicyRow.max_concurrent_sessions` 또는 `KeyPairResourcePolicyRow.max_concurrent_sftp_sessions` where `KeyPairResourcePolicyRow.name == resource_policy_name`

**외부 쿼리**:
- Redis/Valkey: `sched_ctx.registry.valkey_stat.check_keypair_concurrency()`

**필요한 데이터**:
- KeyPair의 리소스 정책 이름
- 리소스 정책의 최대 동시 세션 제한
- Redis/Valkey에서 현재 동시 실행 사용량
- 세션의 `is_private` 플래그 (sess_ctx에서)
- 세션의 `access_key` (sess_ctx에서)

## 3. check_dependencies
**목적**: 모든 종속 세션이 성공적으로 완료되었는지 확인

**데이터베이스 쿼리**:
- `SessionDependencyRow`와 `SessionRow`를 `SessionDependencyRow.depends_on == SessionRow.id`로 조인
- `SessionRow.id`, `SessionRow.name`, `SessionRow.status`, `SessionRow.result` 선택
- `SessionDependencyRow.session_id == sess_ctx.id` 조건

**필요한 데이터**:
- 종속 세션 목록과 각각의 상태 및 결과
- 현재 세션의 `id` (sess_ctx에서)

## 4. check_keypair_resource_limit
**목적**: keypair가 충분한 리소스 할당량을 가지고 있는지 확인

**데이터베이스 쿼리**:
1. `KeyPairRow.resource_policy` where `KeyPairRow.access_key == sess_ctx.access_key`
2. `KeyPairResourcePolicyRow` where `KeyPairResourcePolicyRow.name == resource_policy_name`

**외부 쿼리**:
- `sched_ctx.registry.get_keypair_occupancy(sess_ctx.access_key, db_sess=db_sess)`

**필요한 데이터**:
- KeyPair의 리소스 정책
- 리소스 정책의 `total_resource_slots`와 `default_for_unspecified`
- 현재 keypair 리소스 사용량
- 세션의 `access_key`와 `requested_slots` (sess_ctx에서)
- 알려진 슬롯 타입들 (sched_ctx에서)

## 5. check_user_resource_limit
**목적**: 사용자의 메인 keypair가 충분한 리소스 할당량을 가지고 있는지 확인

**데이터베이스 쿼리**:
1. `UserRow.main_access_key` where `UserRow.uuid == sess_ctx.user_uuid`
2. `KeyPairRow.resource_policy` where `KeyPairRow.access_key == main_access_key`
3. `KeyPairResourcePolicyRow` where `KeyPairResourcePolicyRow.name == resource_policy_name`

**외부 쿼리**:
- `sched_ctx.registry.get_user_occupancy(sess_ctx.user_uuid, db_sess=db_sess)`

**필요한 데이터**:
- 사용자의 메인 액세스 키
- 메인 keypair의 리소스 정책
- 리소스 정책의 `total_resource_slots`와 `default_for_unspecified`
- 현재 사용자 리소스 사용량
- 세션의 `user_uuid`와 `requested_slots` (sess_ctx에서)
- 알려진 슬롯 타입들 (sched_ctx에서)

## 6. check_group_resource_limit
**목적**: 그룹이 충분한 리소스 할당량을 가지고 있는지 확인

**데이터베이스 쿼리**:
- `GroupRow.total_resource_slots` where `GroupRow.id == sess_ctx.group_id`

**외부 쿼리**:
- `sched_ctx.registry.get_group_occupancy(sess_ctx.group_id, db_sess=db_sess)`

**필요한 데이터**:
- 그룹의 `total_resource_slots`
- 현재 그룹 리소스 사용량
- 세션의 `group_id`와 `requested_slots` (sess_ctx에서)
- 알려진 슬롯 타입들 (sched_ctx에서)

## 7. check_domain_resource_limit
**목적**: 도메인이 충분한 리소스 할당량을 가지고 있는지 확인

**데이터베이스 쿼리**:
- `DomainRow.total_resource_slots` where `DomainRow.name == sess_ctx.domain_name`

**외부 쿼리**:
- `sched_ctx.registry.get_domain_occupancy(sess_ctx.domain_name, db_sess=db_sess)`

**필요한 데이터**:
- 도메인의 `total_resource_slots`
- 현재 도메인 리소스 사용량
- 세션의 `domain_name`과 `requested_slots` (sess_ctx에서)
- 알려진 슬롯 타입들 (sched_ctx에서)

## 8. check_pending_session_count_limit
**목적**: 사용자가 최대 대기 중인 세션 수 제한에 도달했는지 확인

**데이터베이스 쿼리**:
1. `SessionRow` where `SessionRow.access_key == sess_ctx.access_key` AND `SessionRow.status == SessionStatus.PENDING`
   - 옵션: `noload("*"), load_only(SessionRow.requested_slots)`
2. `KeyPairResourcePolicyRow`와 `KeyPairRow`를 `KeyPairResourcePolicyRow.name == KeyPairRow.resource_policy`로 조인
   - `KeyPairResourcePolicyRow` 선택 where `KeyPairRow.access_key == sess_ctx.access_key`
   - 옵션: `noload("*"), load_only(KeyPairResourcePolicyRow.max_pending_session_count)`

**필요한 데이터**:
- 액세스 키에 대한 대기 중인 세션 목록
- 리소스 정책의 `max_pending_session_count`
- 세션의 `access_key` (sess_ctx에서)

## 9. check_pending_session_resource_limit
**목적**: 사용자가 최대 대기 중인 세션 리소스 제한에 도달했는지 확인

**데이터베이스 쿼리**:
1. `SessionRow` where `SessionRow.access_key == sess_ctx.access_key` AND `SessionRow.status == SessionStatus.PENDING`
   - 옵션: `noload("*"), load_only(SessionRow.requested_slots)`
2. `KeyPairResourcePolicyRow`와 `KeyPairRow`를 `KeyPairResourcePolicyRow.name == KeyPairRow.resource_policy`로 조인
   - `KeyPairResourcePolicyRow` 선택 where `KeyPairRow.access_key == sess_ctx.access_key`
   - 옵션: `noload("*"), load_only(KeyPairResourcePolicyRow.max_pending_session_resource_slots)`

**필요한 데이터**:
- 대기 중인 세션 목록과 각각의 `requested_slots`
- 리소스 정책의 `max_pending_session_resource_slots`
- 세션의 `access_key` (sess_ctx에서)
- 알려진 슬롯 타입들 (sched_ctx에서)

## 요약

`db_sess`를 전달하지 않고 validator를 구현하려면 다음 데이터를 미리 가져와야 함:

1. **세션별 데이터**:
   - 세션 속성들 (sess_ctx에서)
   - 세션의 starts_at 타임스탬프 (배치 세션용)
   - 세션의 종속성과 그들의 상태 및 결과

2. **정책 데이터**:
   - KeyPair의 리소스 정책
   - 리소스 정책 세부사항 (제한, 할당량)
   - 사용자의 메인 keypair와 그 리소스 정책
   - 그룹의 리소스 제한
   - 도메인의 리소스 제한

3. **현재 사용량 데이터**:
   - Keypair 동시 실행 사용량 (Redis/Valkey에서)
   - Keypair 리소스 사용량
   - 사용자 리소스 사용량
   - 그룹 리소스 사용량
   - 도메인 리소스 사용량
   - 대기 중인 세션 목록과 그들의 리소스 사용량

4. **시스템 구성**:
   - 알려진 슬롯 타입들 (sched_ctx에서)