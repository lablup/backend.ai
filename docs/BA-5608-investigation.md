# BA-5608: Session owner_access_key - Scaling Group Error & Owner Context Bug

- PR: https://github.com/lablup/backend.ai/pull/10824
- Branch: `fix/BA-5608-session-owner-user-scope`
- Jira: https://lablup.atlassian.net/browse/BA-5608

## Reported Issues

1. **Scaling group error**: session owner 설정해서 배포할 때 scaling group 에러 발생 (실제 권한이 있어도 접근 불가)
2. **Session owner 미동작**: owner_access_key를 설정해도 세션이 올바르게 동작하지 않음

## Root Cause

`services/session/service.py`의 세션 생성 메서드 3개 (`create_from_params`, `create_from_template`, `create_cluster`)에서 `UserScope`를 구성할 때, `owner_access_key`가 지정되어도 **요청자(requester)**의 `user_uuid`와 `user_role`을 사용하고 있었음.

### Bug Location (수정 전)

```python
# services/session/service.py - create_from_params (line 519-524)
owner_uuid, group_id, resource_policy = await self._session_repository.query_userinfo(
    user_id, requester_access_key, user_role, domain_name,
    keypair_resource_policy, domain_name, group_name,
    query_on_behalf_of=owner_access_key,
)

resp = await self._agent_registry.create_session(
    session_name,
    image_row.image_ref,
    UserScope(
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_id,      # BUG: requester의 UUID (admin)
        user_role=user_role,     # BUG: requester의 role (superadmin)
    ),
    owner_access_key,
    ...
)
```

`query_userinfo()`가 반환한 `owner_uuid`를 사용하지 않고, action에서 전달된 `user_id` (요청자 UUID)를 그대로 사용.

### Impact

`UserScope.user_uuid`는 다음 위치에서 사용됨:

1. **`registry.py:440`** - 커스텀 이미지 소유자 검증 (`user:{user_scope.user_uuid}`)
2. **`registry.py:543`** - container UID/GID 조회 (`UserRow.uuid == user_scope.user_uuid`)
3. **`preparer.py:129`** - DB에 저장되는 session의 `user_uuid` 설정
4. **`preparer.py:257`** - kernel의 `user_uuid` 설정

## Fix

### 1. `query_userinfo` 반환값 확장 (utils.py)

기존: `(owner_uuid, group_id, resource_policy)` 3-tuple
변경: `(owner_uuid, group_id, resource_policy, owner_role)` 4-tuple

`query_userinfo` 내부에서 이미 `owner_role`을 DB에서 조회하고 있었으나 반환하지 않고 있었음.

### 2. UserScope 구성 수정 (service.py)

```python
# 수정 후
owner_uuid, group_id, resource_policy, owner_role = (
    await self._session_repository.query_userinfo(...)
)

UserScope(
    domain_name=domain_name,
    group_id=group_id,
    user_uuid=owner_uuid,        # FIX: owner의 UUID
    user_role=str(owner_role),   # FIX: owner의 role
)
```

3개 메서드 모두 동일하게 수정:
- `create_from_params`
- `create_from_template`
- `create_cluster`

### 3. 기타 호출자 업데이트

- `model_serving/repository.py`: 반환된 `owner_role` 활용, 중복 DB 쿼리 제거
- `event_dispatcher/handlers/model_serving.py`: 4-tuple 언패킹
- `repositories/deployment/db_source/db_source.py`: 4-tuple 언패킹

## Changed Files

| File | Change |
|------|--------|
| `src/ai/backend/manager/utils.py` | `query_userinfo`, `query_userinfo_from_session` 반환값에 `owner_role` 추가 |
| `src/ai/backend/manager/repositories/session/db_source/db_source.py` | 래퍼 반환 타입 업데이트 |
| `src/ai/backend/manager/repositories/session/repository.py` | 래퍼 반환 타입 업데이트 |
| `src/ai/backend/manager/services/session/service.py` | 3개 메서드에서 UserScope에 owner 컨텍스트 사용 |
| `src/ai/backend/manager/repositories/model_serving/repository.py` | 반환된 owner_role 활용, 중복 쿼리 제거 |
| `src/ai/backend/manager/event_dispatcher/handlers/model_serving.py` | 4-tuple 언패킹 |
| `src/ai/backend/manager/repositories/deployment/db_source/db_source.py` | 4-tuple 언패킹 |
| `tests/unit/manager/services/session/test_session_lifecycle_service.py` | mock return value 업데이트 |

## Reproduction & Verification

### Test Script

`scripts/test_owner_access_key.py` - HMAC 인증으로 직접 REST API 호출

- Test 1: Admin이 자신의 세션 생성 (정상 케이스)
- Test 2: Admin이 `owner_access_key`로 일반 사용자 대신 세션 생성

### 수정 전 결과

```
# Test 2 세션의 DB 레코드:
name=test-delegated-104605 | user_uuid=f38dea23... | email=admin@lablup.com | access_key=AKIANABBDUSEREXAMPLE
                                                     ^^^^^^^^^^^^^^^^^^^^^^^^
                                                     BUG: admin UUID가 저장됨
                                                     (user@lablup.com이어야 함)
```

같은 session_name으로 재생성 시 unique constraint 에러에서도 확인:
```
duplicate key value violates unique constraint "ix_sessions_unique_name_per_user_nonterminal"
Key (name, user_uuid)=(test-owner-104550, f38dea23-...) already exists.
                                           ^^^^^^^^^^
                                           admin UUID
```

### 수정 후 결과

```
# Test 1 (admin 자신):
name=test-owner-104920     | user_uuid=f38dea23... | email=admin@lablup.com | access_key=AKIAIOSFODNN7EXAMPLE

# Test 2 (delegated):
name=test-delegated-104920 | user_uuid=dfa9da54... | email=user@lablup.com  | access_key=AKIANABBDUSEREXAMPLE
                                                     ^^^^^^^^^^^^^^^^^^^^^^^
                                                     FIX: user UUID가 올바르게 저장됨
```

### Scaling Group Issue Note

로컬 개발 환경에는 scaling group이 `default` 하나만 있어서 scaling group 접근 에러를 직접 재현하기 어려움. 프로덕션에서 여러 scaling group이 있고 keypair/group별 권한이 다를 때, `UserScope`의 잘못된 `user_uuid`로 인해 `registry.py`에서 잘못된 UserRow를 조회하면서 연쇄적으로 문제가 발생할 수 있음. 참고로 `from_deployment_info` (deployment 경로)에서는 이미 올바르게 owner context를 사용하고 있었음.
