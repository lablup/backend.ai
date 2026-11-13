# 엔티티 카탈로그

이 패키지는 종류마다 `EntityType` 또는 `FieldType` 서브클래스를 하나 둔다. 클래스는 `name()` 과
`description()` 을 반환하고, 필드 종류는 row 를 소유하는 엔티티 종류를 `owner_type()` 으로 반환한다. 소유자 종류가
고정되지 않는 필드 종류(audit_log, audit_log_scope, label, secret, fair share 3종)는 `DanglingFieldType` 을
상속해 `None` 을 반환한다. 무엇을 소유하고 무엇에 묶이는지는 이 문서에 적는다. 전부 개념 수준이며, 어느
테이블이 담는지는 `models` 문서가 맡는다.

## 타입 값 규칙

- 값은 사용처에서 `AgentEntityType()` 처럼 인자 없이 생성한다. 모듈 인스턴스 상수를 두지 않는다.
- 필드 종류는 `owner_type()` 으로 row 를 소유하는 엔티티 종류를 반환한다. 소유자가 row 의 값이라 고정되지
  않으면 `DanglingFieldType` 을 상속해 `None` 을 반환한다.
- `EntityType(value)` 는 base 인스턴스를 생성하며 `name()` 과 `description()` 을 반환하지 않는다. 문자열을 읽는
  경계(row column, legacy 액션, RBAC 요소)에서만 사용하고 그 밖에서는 생성하지 않는다.
- pydantic 은 base 로 선언한 필드면 문자열을 그대로 받고, 종류로 선언한 필드면 그 이름만 받는다. row 에는
  `name()` 문자열이 저장된다.
- secret 은 여러 엔티티의 암호화된 column 에 저장된 필드이며 소유자 종류가 고정되지 않는다. 자체 row 없이
  상태 조회와 재암호화를 수행한다.

## 엔티티

어딘가에 속하는 엔티티다. 공통 루트가 없고 여러 엔티티가 맨 위에 있다.

```
domain
├── auto-generated file  (owned by domain)
├── project
│   ├── session
│   ├── session group
│   ├── deployment
│   ├── network
│   ├── vfolder          (owned by project)
│   ├── auto-generated file  (owned by project)
│   ├── model card
│   └── role
└── user
    ├── vfolder          (owned by user)
    ├── auto-generated file  (owned by user)
    └── role

resource group
└── agent

container registry
└── image
```

### domain

| 관계 | 대상 |
|---|---|
| field | usage bucket |

### project

| 관계 | 대상 |
|---|---|
| field | usage bucket |

### user

| 관계 | 대상 |
|---|---|
| field | keypair, error log, login session, login history, usage bucket |
| reference | resource policy |

### session

| 관계 | 대상 |
|---|---|
| field | kernel, kernel group, kernel group resource slot |
| reference | image, vfolder, session group, resource group |

### deployment

| 관계 | 대상 |
|---|---|
| field | replica group, replica, deployment revision, deployment policy |
| reference | image, vfolder, runtime variant, deployment revision preset, session group, resource group, prometheus query preset |

### model card

| 관계 | 대상 |
|---|---|
| reference | vfolder |

### role

| 관계 | 대상 |
|---|---|
| field | permission |

### resource group

| 관계 | 대상 |
|---|---|
| field | fair share |

### agent

| 관계 | 대상 |
|---|---|
| field | agent resource |

### image

| 관계 | 대상 |
|---|---|
| field | image alias |

## public 엔티티

읽기에는 인증만 필요하고, 생성, 변경, 삭제는 admin 전용이다.

### 실행 스펙

| 엔티티 | 고르는 대상 |
|---|---|
| runtime variant | deployment revision |
| runtime variant preset | runtime variant 를 참조한다 |
| deployment revision preset | deployment revision |
| session template | session |
| resource preset | session |
| resource slot type | agent resource |

### 인증

| 엔티티 | 고르는 대상 |
|---|---|
| login client type | login session |

## global

읽기와 쓰기 모두 admin 전용이다.

### 정책

| 엔티티 | field | reference |
|---|---|---|
| resource policy | | |
| retention policy | | |
| role preset | role permission preset | |

### 아티팩트

```
artifact registry
└── artifact
```

| 엔티티 | field | reference |
|---|---|---|
| artifact registry | huggingface registry, reservoir registry | |
| artifact | | storage namespace |

### 스토리지

| 엔티티 | field | reference |
|---|---|---|
| storage namespace | object storage, vfs storage | |

### 관측

| 엔티티 | field | reference |
|---|---|---|
| audit log | | |
| event log | | |
| prometheus query preset | | prometheus query preset category |
| prometheus query preset category | | |

### 알림

| 엔티티 | field | reference |
|---|---|---|
| notification channel | | |
| notification rule | | notification channel |

### 설정과 운영

| 엔티티 | field | reference |
|---|---|---|
| app config definition | | |
| app config allow list | app config fragment | app config definition |
| idle checker | | |
| service catalog | | |

## 할당

관리자가 공유 자원을 스코프에 할당한다. 어느 쪽도 다른 쪽을 포함하지 않으므로 virtual entity 간선이 아니고,
할당 테이블은 엔티티 자체가 아니라 두 엔티티 사이의 relation 이다.

### resource group

| 할당받는 쪽 |
|---|
| domain |
| project |
| keypair |

### idle checker

| 할당받는 쪽 |
|---|
| domain, project, user |

## 할당 외래 키는 양쪽 모두 RESTRICT 다

- 소유가 아니므로 한쪽을 삭제해도 다른 쪽은 삭제되지 않는다. 다만 의존이 커서 연결된 엔티티를
  이동할 것인지 삭제할 것인지는 애플리케이션이 결정한다.
- RESTRICT 는 그 결정을 애플리케이션으로 전달한다. 데이터베이스가 조용히 정리하면 그 결정을 내릴 지점이
  사라진다.

## virtual 엔티티

자체 row 없이 생성한다. 감사와 권한 부여의 대상으로만 존재한다.

| 엔티티 | 읽는 곳 |
|---|---|
| app config | 읽는 스코프 |

## 범위 밖

virtual entity 는 소유를 표현하는 계층이지 엔티티가 아니다.

### 노드를 지정하는 값

- 그래프 간선 테이블 두 개(`entity_memberships`, `scope_bindings`)는 양끝을 `virtual_entities.id` 외래
  키로 지정한다. 스코프도 엔티티이고 자기 노드를 가지므로 binding 의 스코프 쪽도 노드 외래 키다. 노드를
  삭제하면 그 간선까지 연쇄 삭제된다.
- `permissions` / `field_permissions` 는 스코프 쌍을 유지한다. 엔티티가 아닌 global 스코프를 지정해야
  하기 때문이다.
- `entity_labels` / `entity_invitations` 는 `(entity_type, entity_id)` 쌍을 유지한다. 그래프 간선이 아니라
  엔티티의 속성이고, 그 쌍의 인덱스가 읽기를 바로 반환하며, 노드가 없는 legacy 엔티티에도 붙어야 한다.
  노드를 거치면 읽기마다 노드 확인이 하나씩 늘고 노드가 전제 조건이 된다.
- 노드 id 는 repository 계층 안에만 둔다. `data/` 타입과 service 결과는 엔티티를 `EntityIdentifier` 하나로
  전달하고 노드 id 는 전달하지 않는다.
- 노드는 `(entity_type, entity_id)` 유일 인덱스나 기본 키로 조회한다. `entity_id` 만으로 조회하면 인덱스를
  사용할 수 없으므로 그런 조회는 생성하지 않는다.

## 외래 키가 없는 relation

외래 키를 선언하지 않은 소유 관계다.

- artifact → artifact registry (`registry_id`, `source_registry_id`)
- artifact registry → huggingface / reservoir registry (`registry_id`, polymorphic)
- deployment revision → deployment (`endpoint`)
- storage namespace → object storage 또는 vfs storage (`storage_id`, polymorphic, discriminator 없음)
- association_artifacts_storages → artifact revision, storage namespace
- network → project

## 방향: 식별자를 엔티티 축으로 모은다

대부분의 id 타입은 엔티티나 필드를 식별하므로 타입 클래스와 같은 파일에 선언한다. 그러면 둘 중 하나만 추가해도
파일을 열어 보는 것만으로 드러나고, 타입 클래스가 없는 파일 자체가 신호가 된다. 필드이거나 아직 분류되지
않은 상태다.

- 스코프 식별자는 엔티티 식별자의 별칭이므로 이 축에 둔다.
- 엔티티를 식별하지 않는 값 타입은 함께 옮기지 않는다. architecture 이름이나 실행 하나를 지정하는 id 같은
  값은 base 타입에 둔다.
- 엔티티마다 패키지를 두고 세부를 파일로 나누면 관련된 것을 나중에 그 아래로 옮길 여지가 생긴다.
