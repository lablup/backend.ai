# 프로젝트 멤버십

## 관련 이슈

- BEP-1075 (Entity Relation Operations): 이 문서가 사용하는 relation 기록 프리미티브
- BA-7467 (action 이 엔티티를 지정하는 방법)

## 동기

사용자를 프로젝트에 추가하는 일은 두 가지를 한다. relation 을 추가하고 역할을 부여한다. 지금은 이 둘이
결합해 있고, user id 를 모르는 사람에게는 그 동작을 실행할 수 없다.

- 가입은 항상 scope 의 `auto_assign` 역할을 함께 가져오므로 멤버십과 역할 상태를 구분할 수 없다
- user id 가 필요하므로 아직 계정이 없는 사람은 추가할 수 없다

다른 사람에게 권한을 전달하는 일에는 이미 즉시와 초대 두 갈래가 있다. 프로젝트 멤버십도 같은 짝을
가진다.

## 현재 설계

### 현재의 멤버십

| | 현재 |
|---|---|
| 테이블 | `association_groups_users`. `DEPRECATED` 이며 `association_scopes_entities` 로 옮기는 중 |
| 역할 | `ScopeUserMember.assign_role_on()` 이 가입할 때마다 scope 의 `auto_assign` 역할을 부여한다 |
| 지정 | user id 가 필요하다 |

`ScopeUserMember` 는 그 결합 자체를 밝힌다. *"멤버십은 항상 scope 의 auto_assign 역할을 (멱등하게)
부여하므로 멤버십과 역할 상태는 어긋날 수 없다."*

`UserUpdater.group_ids` 는 편집 경로로 같은 멤버십을 전달한다. column 이 아니므로 기록 경로가
`build_values()` 옆에서 이를 동기화한다 (BEP-1075).

### domain 은 이 모양이 아니다

사용자는 정확히 하나의 domain 에 속하고, 그 값은 foreign key 를 가진 `users.domain_id` 에 있다.
domain 과 user 를 잇는 relation 테이블은 없고 column 은 `NOT NULL` 이다.

| | 프로젝트 | domain |
|---|---|---|
| 저장 | `association_groups_users` | `users.domain_id` column |
| 다중도 | 다대다 | 일대다 |

따라서 domain 은 초대 대상이 아니다. 사용자는 domain 아래에서 생성되고, domain 사이를 옮기는 일은
멤버십 동작이 아니라 사용자의 편집이다. 이 제안은 프로젝트만 다룬다.

### 이미 있는 초대

`entity_shares` 는 **엔티티에 대한 접근**을 제공한다.

| column | 값 |
|---|---|
| `target_entity_type`, `target_entity_id` | polymorphic, foreign key 없음 |
| `permission_cap` | 수락할 때 적용되는 상한 |
| `invitee_email` | email. 아직 계정이 없는 사람을 지정한다 |
| `status` | `pending` 인 동안에만 unique |

프로젝트 멤버십은 그 모양에 맞지 않는다. 전달할 값이 상한이 아니라 역할이고, 수락이 기록하는 것도
다르다.

## 제안 설계

### 갈래 둘

| | 효력 발생 시점 | 지정 | 상대방 계정 |
|---|---|---|---|
| grant | 즉시 | user id | 있어야 한다 |
| 초대 | 수락 시 | email | 없어도 된다 |

권한을 전달할 때와 같은 짝이다.

### 각 갈래가 하는 일

```
1. add the relation      project ↔ user
2. grant the role        the named role if there is one, otherwise the project's auto_assign roles
```

하나의 트랜잭션 안에서 기록 두 번이지 하나의 사실이 아니다. 그래서 `ScopeUserMember` 의 결합이
풀린다.

### 역할은 그 프로젝트의 역할 중에서 고른다

그 프로젝트의 scope 에 등록된 역할만 지정할 수 있다. 그렇지 않으면 멤버십이 무관한 역할을 추가하는
경로가 된다.

### 권한

사용자를 프로젝트 안에 추가하는 일에서 scope 는 **하나**다.

| 축 | 값 |
|---|---|
| `scope_targets()` | 그 프로젝트 |
| `entity_type()` | `user` |

역할을 지정하면 하나가 추가된다.

| | 요구하는 것 |
|---|---|
| 역할을 지정하지 않음 (`auto_assign`) | 프로젝트 scope 의 `user` 권한 |
| 역할을 지정함 | 그것에 추가로 **그 역할을 부여할 권한** |

자기가 부여할 수 없는 역할은 아무도 추가할 수 없다.

### 제거

```
remove the relation  +  take back the roles enrolled in that project from this user
```

**어느 역할이 이 멤버십에서 왔는지 기록할 필요가 없다.** 역할은 그 프로젝트 자신의 것 중에서만
고를 수 있으므로, 그 프로젝트의 멤버가 아니면서 프로젝트 scope 역할을 보유하는 상태는 생기지 않는다.
회수하는 것은 "그 프로젝트에 등록된 역할"과 이 사용자가 보유한 역할의 교집합이다.

이 조회는 이미 있다. `ScopedRoleOperationScope` 가 한 scope 에 등록된 역할을 고른다.

감사 로그는 관찰용이다. 회수할 것을 감사 로그 row 에서 읽지 않는다. 감사 로그는 retention 정리로
삭제된다.

### 초대는 별도 테이블을 가진다

`entity_shares` 와 다른 축이다.

| | `entity_shares` | 프로젝트 초대 |
|---|---|---|
| 제공하는 것 | 엔티티에 대한 접근 | 프로젝트 멤버십 |
| 전달하는 값 | `permission_cap` | 역할 또는 `auto_assign` |
| 수락 시 기록 | 멤버십 row 하나 | relation 과 역할 |

형식은 같다. email 로 지정하고, 수락하거나 거절하며, pending 인 동안에만 unique 다.

**수락 뒤에는 초대와 상태가 갈라진다.** 초대를 삭제해도 relation 과 역할은 남는다. 초대는 제공이지
권한이 아니며, 권한 초대가 따르는 것과 같은 규칙이다.

## 이전과 호환

- `ScopeUserMember` 의 역할 결합을 되돌린다. 역할 부여는 멤버십 동작의 두 번째 단계가 된다
- `UserUpdater` 에서 `group_ids` 를 제거한다. 프로젝트에 등록하는 일은 자체 동작이다
- `association_groups_users` 를 `association_scopes_entities` 로 옮기는 일을 중단한다. 프로젝트
  멤버십은 업무상 relation 이지 권한 graph 를 위한 사실이 아니다 (BEP-1075)
- relation row 는 BEP-1075 의 relation 프리미티브로 기록한다. service 가 그것을 역할 부여와 조합한다

## 구현 계획

이 BEP 가 확정된 뒤에 정한다.

## 열린 질문

- 초대 테이블이 역할을 전달하는 방식. 역할 id column 하나를 두는 방식과 "지정 없음(`auto_assign`)"을
  구분하는 방법
- 받은 초대가 두 테이블에 걸쳐 있다. 사용자에게 목록 하나를 보여주려면 둘을 합칠 곳이 필요하다
- 초대 시점에 지정한 역할이 수락 시점에 없을 때의 처리
- `UserUpdater.domain_name` 은 사용자의 편집으로 남지만 이동이다. 식별자가 `domain_id` 가 되고(경계에서
  lookup 으로 이름을 조회해 변경한다), 이동이 그 밖에 전달할 값(권한 graph 멤버십, 이전 domain 의
  프로젝트, session 과 vfolder 에 복사된 domain)에 대한 결정은 여기서 하지 않는다
