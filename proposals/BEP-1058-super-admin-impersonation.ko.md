# superadmin 사용자 가장

## 관련 이슈

- JIRA: BA-6779 (이 BEP)
- Epic: BA-6778. superadmin 사용자 가장: trigger 주체와 effective user 권한 주체를 분리한다

## 1. 목표

superadmin 이 동작을 **trigger** 하면서 그 동작은 **대상 사용자의 권한 맥락에서 실행**하게 한다. 그 사용자가 할 수 있는 일만 허용된다. 동시에 감사 기록에는 **두 주체**를 남긴다: trigger 한 superadmin 과 실제로 실행한 신원이다.

용도: 지원과 디버깅(이 사용자가 왜 X 를 할 수 없는지 그대로 재현), 권한 검증.

## 2. 동기

지금 Backend.AI 는 **인증한 요청자**와 **권한을 평가하는 주체**를 하나의 신원으로 다룬다. `current_user()` 는 `ContextVar[UserData]` 하나이고, 인증 middleware 가 keypair 하나로 채운다. 그래서 superadmin 은 주어진 사용자의 관점에서 동작을 재현할 방법이 없다. RBAC 우회(`if user.is_superadmin: return`)로 무조건 통과하거나, `owner_access_key` 로 **자기 권한으로** 실행할 뿐 **대상의 권한으로** 실행하지는 못한다.

## 3. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 3.1 신원 맥락

| | 항목 |
|---|---|
| ✅ | `current_user() -> UserData \| None` 하나(`common/contexts/user.py`). field: user_id / is_authorized / is_admin / is_superadmin / role / domain_name |
| ✅ | 유일한 writer 는 인증 middleware `_setup_user_context`(`manager/api/rest/middleware/auth.py`)다. `with_user(UserData(...))` 를 호출한다 |
| ➕ | 전용 **trigger 사용자** 접근자 `triggered_user()` 와 `with_triggered_user()`(별도 ContextVar) |

### 3.2 인증 middleware 와 가장 신호

| | 항목 |
|---|---|
| ✅ | global middleware 가 HMAC / JWT / hook 으로 인증한 뒤 `_setup_user_context` 에서 맥락을 주입한다 |
| ✅ | 기존 위임 신호 `owner_access_key` 는 **요청 body/query parameter** 다(엔드포인트마다 처리하며 session/vfolder/model-serving 계열에만 있다) |
| ➕ | 새 가장 신호는 **HTTP header** `X-BackendAI-Act-As`(대상 UUID)이고, 인증 직후 middleware 에서 전역으로 해석한다 |

### 3.3 RBAC 적용

| | 항목 |
|---|---|
| ✅ | `ScopeActionRBACValidator` 같은 validator 가 `current_user()` 를 읽고 `if user.is_superadmin: return` 으로 즉시 반환한다 (`actions/validators/rbac/{scope,single_entity,bulk,legacy}.py`, `auth_validator.py`) |
| ✅ | 스코프 판정: 많은 adapter, resolver, service, repository 가 `current_user()` 를 "my" 스코프로 사용한다 |
| ➕ | **코드 변경 없음**. 가장 중에는 `current_user()` 가 대상을 참조하므로 적용과 스코프 판정이 자동으로 대상 기준이 된다 (4.3 권한과 스코프 의미) |

### 3.4 귀속

| | 항목 |
|---|---|
| ✅ | 감사 `audit_logs` 의 주체는 **nullable column 하나** `triggered_by` = `current_user().user_id` 다 (`actions/monitors/audit_log.py`, `models/audit_log/row.py`) |
| ✅ | 세션 소유자 기록: `assign_user_identity_rule.py` 가 `current_user()` 로 세션 소유자 uuid 를 지정한다 |
| ✅ | event 전파: `common/events/dispatcher.py` 가 async handler 에 `current_user()` 를 다시 주입한다 |
| ➕ | `audit_logs` 에 **nullable** `acted_as` column 을 추가하고 `triggered_by` 의 뜻을 다시 정의한다 (4.5 감사 모델) |
| ➕ | event dispatcher 가 `triggered_user()` 도 전파한다(background 감사 일관성) |

### 3.5 기존 위임 (owner_access_key)

| | 항목 |
|---|---|
| ✅ | `resolve_access_key_scope` 와 `query_userinfo(query_on_behalf_of=...)` 는 대상에서 **정책 맥락(자원 할당 등)** 만 채운다. 권한 평가 주체는 요청자로 남고 감사도 마찬가지다 (`manager/utils.py`, `services/auth`) |
| ✅ | 자격 검사 `check_if_requester_is_eligible_to_act_as_target_user` 는 **service-validator 계층**에서 role/domain 을 검사한다 |
| ➕ | 가장과 **공존한다**. owner_access_key 는 정책만 위임하고, 이 작업은 실행 주체 자체를 위임한다. 위임 대상이 다르다 (4.4 owner_access_key 와의 관계) |

## 4. 제안 설계

### 4.1 두 신원 맥락 모델

맥락에 신원 두 개를 담는다.

| 신원 | 뜻 | 접근자 | 일반 요청 | 가장 |
|----------|---------|----------|----------------|---------------|
| **effective (acting) 사용자** | 권한과 스코프의 주체. 기존 모든 동작이 이 신원을 기준으로 한다 | `current_user()` (유지) | = 인증 사용자 | = 대상 |
| **trigger 사용자** | 인증한 호출자 | `triggered_user()` (신규) | = 인증 사용자 | = superadmin |

핵심 계약: **기존 모든 동작은 effective user 만 기준으로 실행한다**. 그 사용자가 바로 `current_user()` 가 가진 값이므로 기존 호출부(수십 개 adapter, resolver, service, repository, RBAC)는 **그대로 둔다**. 일반 요청에서는 두 신원이 같은 `UserData` 를 참조하고, 가장 중에만 갈라진다.

```python
# common/contexts/user.py — accessor contract (details in the PR)
def current_user() -> UserData | None: ...          # existing: effective (acting) subject
def triggered_user() -> UserData | None: ...          # new: trigger (requesting) subject
def with_triggered_user(user: UserData) -> ...: ...   # new context manager
```

> 이름에 대한 메모: `current_user` 는 "현재 권한과 스코프의 주체", 즉 effective user 를 의미하고 **호출자를 의미하지 않는다**. docstring 에 이를 분명히 적는다. (이름 변경은 검토했다. 결정 기록 참조.)

### 4.2 가장 신호와 middleware 순서

- 신호: `X-BackendAI-Act-As: <target user UUID>` header. **UUID 만** 받는다(편의 식별자 없음). 전송 계층 신호이므로 REST v2 와 GraphQL 에서 똑같이 동작하고 DTO 변경이 없다.
- 위치: **사용자 인증이 확인된 직후의 middleware**. 전역으로 적용되므로 요청 전체가 대상으로 실행된다(fail-closed). 어떤 엔드포인트도 superadmin 의 권한을 흘리지 못한다.

middleware 순서(계약):

```
authenticate (HMAC/JWT/hook) → resolve Act-As
  ├ no header  : current_user = triggered_user = authenticated
  └ header set : verify the authenticated caller is superadmin → load target UserData (DB)
                 current_user = target,  triggered_user = authenticated
→ push with_user(current) + with_triggered_user(trigger) → handler
```

- superadmin 이 아니거나 대상을 찾지 못하면 요청을 거부한다 (4.6 자격).

### 4.3 권한과 스코프 의미 (변경이 작은 이유)

가장 중에는 `current_user()` 가 대상의 **전체 `UserData`**(대상의 role, is_superadmin, domain_name)를 가진다. 따라서:

- RBAC 우회 `if user.is_superadmin: return` 이 대상 기준으로 평가된다. 대상이 일반 사용자이면 우회가 사라지고 동작은 **대상의 scope-chain 권한으로 제한된다**(의도한 의미 그대로다).
- **`my_*` self-service 동작**(예: `my_keypairs`, `my_user_v2`)은 내부에서 `current_user()` 로 "my" 스코프를 해석한다. 따라서 가장 중에는 읽기와 쓰기 모두 **실행 주체(대상) 기준으로** 동작한다. superadmin 은 대상의 화면과 자원을 보고 조작한다. superadmin 자신의 신원이 필요하면 `triggered_user()` 를 사용한다.
- GraphQL `me`/viewer 도 대상을 반환한다(superadmin 이 대상의 관점을 재현한다).

이 모든 것은 맥락 값만 교체하면 성립한다. `my_*` 를 포함해 기존 호출부는 변경하지 않는다.

### 4.4 owner_access_key 와의 관계

두 메커니즘은 **서로 다른 것을 위임한다**. 공존한다.

| | 위임 대상 | 권한 주체 | 적용 방식 |
|---|-------------------|--------------------|-------------|
| `owner_access_key` | **정책**(자원 할당 등) | 요청자(superadmin), 불변 | 요청별 parameter |
| 사용자 가장 | **실행 사용자 자체** | 대상 | 전역(맥락) |

- **통합하지 않는다**. owner_access_key 는 요청자의 권한으로 실행하며 대상의 정책만 빌린다. 별개 동작이다. 이 작업은 실행 주체 자체를 전환한다.
- **별도 거부 없이 공존한다**. 가장 중에는 `current_user()` 가 대상이므로 함께 온 `owner_access_key` 는 **대상의** 권한으로 평가된다. 일반 사용자 대상은 owner_access_key 로 위임할 수 없다(기존 service-validator `check_if_requester_is_eligible_to_act_as_target_user` 가 이미 금지한다). 따라서 조합은 다른 모든 동작처럼 RBAC 로 제한되며 전용 middleware/handler 검사가 필요 없다.

### 4.5 감사 모델

`audit_logs` 에 nullable `acted_as` column 하나를 추가하고 주체 기록을 나눈다.

| column | 뜻 | 일반 요청 | 가장 | 시스템 trigger |
|--------|---------|----------------|---------------|----------------|
| `triggered_by` (기존, nullable, 동작 불변) | 요청을 trigger 한 사람 = `triggered_user()` | 인증 사용자 | superadmin | NULL |
| `acted_as` (신규, nullable) | 실제 실행 신원 = `current_user()` | 인증 사용자 (= triggered_by) | 대상 | NULL |

- 감사 monitor 는 `triggered_by` 를 `triggered_user()` 에서, `acted_as` 를 `current_user()` 에서 읽는다. 변경은 `audit_log.py` 한 곳이다. `triggered_by` 를 채우는 로직은 그대로 둔다.
- `acted_as` 가 **nullable** 인 이유는 시스템 trigger 맥락(맥락에 사용자가 없는 background task, 시스템이 개시한 동작)에서 `current_user()` 가 없기 때문이다. `triggered_by` 와 같다.
- 새 correlation id 는 두지 않는다. 기존 `request_id` 를 재사용한다 (BEP-1035 분산 request ID 전파).

### 4.6 자격 (누가 가장할 수 있는가)

- **superadmin 만** 가능하다. middleware 는 `triggered_user().is_superadmin` 만 검사한다.
- 도메인 관리자는 허용하지 않는다. domain-scope 검사는 RBAC/service-validator 계층에 있고 act-as 는 middleware 계층에서 결정하므로 계층이 다르다. owner_access_key 의 `check_if_requester_is_eligible_to_act_as_target_user` 를 재사용하지 않는 이유도 같다.

## 5. 마이그레이션 / 호환성

- **하위 호환**: header 가 없으면 `triggered_user() == current_user()` 이므로 `triggered_by` 와 `acted_as` 가 같은 값을 가진다. 기존 동작과 감사 의미는 바뀌지 않는다.
- **DB**: `audit_logs.acted_as` nullable column 을 추가한다(Alembic). **기존 row 는 `triggered_by` 로 소급해 채운다**(과거에는 호출자와 effective user 가 같았다). `triggered_by` 가 없는 row(시스템 trigger)는 NULL 로 둔다. 하위 버전에 적용할 때 migration 을 멱등으로 유지한다(`alembic/README.md`).
- **호환성을 깨는 변경은 없다**. 새 접근자와 header 는 추가형이고, schema 변경은 감사 column 뿐이다.

## 6. 구현 계획

1. **맥락과 middleware**: `triggered_user()`/`with_triggered_user()` 를 추가하고 `current_user` docstring 을 분명히 한다(common). `X-BackendAI-Act-As`(UUID)를 해석한다. 인증 뒤 middleware 에서 `is_superadmin` 을 검사하고 대상 UserData 를 읽어 두 맥락을 주입한다. header 처리 자체는 작다.
2. **event dispatcher 전파**: `common/events/dispatcher.py` 가 `current_user()` 와 함께 `triggered_user()` 를 async handler 와 background task 로 전파한다(가장 중 trigger 된 background 작업의 감사 일관성).
3. **감사**: `acted_as` nullable column(Alembic, 기존 row 소급 채움)과 `triggered_by`/`acted_as` 를 나눠 기록하는 monitor.
4. **검증**: 실제 서버에서 superadmin 이 일반 사용자를 가장하면 대상의 권한으로 제한되는지, 감사가 두 주체를 남기는지 확인한다(admin/non-admin).

## 7. 결정 요약

| 결정 | 내용 |
|----------|---------|
| 신원 모델 | `current_user()` = effective(acting)를 유지하고 `triggered_user()` = trigger(요청)를 추가한다. 기존 호출부는 그대로 둔다 |
| 신호 | `X-BackendAI-Act-As` header(UUID 만). 인증 뒤 middleware 에서 전역으로 해석한다(fail-closed) |
| 권한 의미 | 가장 중 `current_user()` 는 대상의 전체 UserData 다. RBAC 우회, 스코프 판정, `my_*` 가 모두 자동으로 실행 주체 기준이 된다 |
| 자격 | superadmin 만 가능하다(middleware 가 is_superadmin 을 검사한다). 도메인 관리자는 허용하지 않는다(계층이 다르다) |
| owner_access_key | 공존한다. 정책 위임과 실행 사용자 위임은 위임 대상이 다르다. 특별 처리는 없다. 가장 중 함께 온 owner_access_key 는 대상의 RBAC 권한으로 제한된다 |
| 감사 | `triggered_by`(기존, 동작 불변) = trigger, 신규 nullable `acted_as` = effective user. 기존 row 는 소급해 채우고 시스템 trigger 는 NULL 로 둔다 |
| 읽기/쓰기 | 가장은 **읽기와 쓰기 모두** 실행 주체(대상) 기준이다. `my_*` 도 포함한다. 쓰기는 대상의 권한 안에서 허용한다(RBAC 로 제한) |
| 상관 | 기존 `request_id` 를 재사용한다. 새 id 는 없다 |

## 결정 기록

| 날짜 | 결정 | 근거 |
|------|----------|-----------|
| 2026-07-08 | trigger 접근자 이름을 `triggered_user()` 로 한다(`request_user` 아님) | 감사 column `triggered_by` 와 맞춘다 |
| 2026-07-08 | `current_user()` 이름을 유지한다(이름 변경은 미룸) | `acting_user()` 로 변경하면 저장소 전체의 기계적 변경이 되어 "최소, 3개 단위" 구현 의도와 충돌한다. 필요하면 나중에 변경할 수 있다 |
| 2026-07-08 | `acted_as` 는 nullable 이다 | 시스템 trigger 맥락에는 `current_user()` 가 없다(맥락에 사용자가 없다). 따라서 `acted_as` 는 NULL 을 허용해야 하고 `triggered_by` 와 같다. 기존 row 는 `triggered_by` 로 소급해 채운다 |
| 2026-07-08 | 자격은 superadmin 만이다 | 도메인 관리자를 허용하려면 domain-scope 검사(RBAC/service-validator)가 필요하지만 act-as 는 middleware 계층에서 결정한다. 계층이 다르다 |
| 2026-07-08 | 가장은 읽기와 쓰기 모두 실행 주체(대상) 기준이다 | 단일 `current_user()` 로 스코프가 정해지므로 자연스럽다. 쓰기는 대상의 권한 안에서 허용한다 |
| 2026-07-08 | `X-BackendAI-Act-As` 와 `owner_access_key` 가 모두 있으면 거부하는 규칙을 제거한다 | 가장 중 `current_user()` 가 대상이므로 함께 온 owner_access_key 는 이미 대상의 권한으로 평가되고 RBAC 로 제한된다(일반 사용자 대상은 위임할 수 없다). 전용 거부는 불필요했고 middleware 와 handler 가 요청별 parameter 를 알아야 했다 |

## 8. 열린 질문

- (없음)

## 9. 참고

- [BEP-1008: RBAC](BEP-1008-RBAC.md), [BEP-1048: RBAC Entity Relationship Model](BEP-1048-RBAC-entity-relationship-model.md): 권한 평가, scope chain
- [BEP-1035: 분산 request ID 전파](BEP-1035-request-id-tracing.md): 주체와 요청 추적
- 선례(기존 위임): `manager/utils.py`, `services/auth` `resolve_access_key_scope`, `query_userinfo(query_on_behalf_of=...)`
