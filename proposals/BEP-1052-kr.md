# Domain Configuration API — GraphQL/REST Schema Proposal (v2)

## Overview

WebUI에서 사용하는 도메인 단위 설정, 공개(로그인 전) 설정, 사용자 개인 설정을 위한
GraphQL / REST API 스키마 제안입니다.

한 스코프(예: 도메인 1개, 사용자 1명) 안에 **여러 개의 named 설정 문서**를
담을 수 있습니다 — 예를 들어 한 도메인은 `theme.json`, `menu.json`,
`branding.json`을 독립적으로 발행할 수 있습니다. 각 문서는
`(scope, scopeId, name)`로 식별됩니다.

## 유저 스토리

- 관리자만이 도메인 전체에 적용할 수 있는 설정이 있다. 이 설정은 사용자가
  변경할 수 없다.
  - 예: theme 관련, 각종 UI의 감춤처리, 추가적인 Menu link, 메뉴 순서 변경
    이나 감춤
  - 도메인 레벨에서만 설정할 수 있는 값 (사용자가 지정할 수 없는 설정 값)
- 도메인 설정 중에는 로그인 없이 조회 가능해야 하는 설정이 있다.
  - 예: theme 관련
- 관리자가 사용자 개인의 설정의 초기값을 도메인별로 지정할 수 있다.
  - 현재 구현된 App Config의 `extraConfig` 필드가 동작하는 방식과 동일.
- 사용자는 개인별 설정을 서버에 저장해서 계정별로 유지되길 바란다.
  - 예: 최근 생성한 세션, 언어, 실험적 기능 사용 여부, Table의 표시 컬럼이나
    순서.
- 같은 스코프가 독립적으로 관리되는 여러 설정 문서(`theme.json`,
  `menu.json` 등)를 발행해야 할 수 있다 — WebUI의 서로 다른 부분에서
  로드되며 버전 관리도 별개.

요약 표:

| Story                                                | Scope                   | 조회               | 수정          |
|------------------------------------------------------|-------------------------|--------------------|---------------|
| Theme, Branding (로그인 전 필요)                     | `public`                | Anyone             | Admin         |
| UI 숨김/표시, 메뉴 설정, 사용자 설정 기본값 (도메인별) | `domain_user_defaults`  | Logged-in users    | Admin         |
| 도메인 한정 내부 관리 설정                           | `domain`                | Admin              | Admin         |
| 사용자 개인 설정                                     | `user`                  | Owner/Admin        | Owner/Admin   |

> `domain` 스코프는 admin-only 정책이라 `myAppConfigs` merge에 들어가지
> 않습니다. 유저가 값을 읽어야 하는 문서("UI 숨김/표시" 등)는
> `domain_user_defaults`에 발행해야 merge 경로로 사용자에게 도달합니다 —
> 자세한 구분은 §5 참고.

## Design Principles

- **Schema-less JSON**: 백엔드는 저장소 역할만 하고, 설정의 구조와 의미는
  프론트엔드가 관리.
- **Scope = Entity**: 권한은 필드가 아닌 스코프(entity)로 분리.
  `global_app_config` (Public 조회 / Admin 수정), `domain_app_config`
  (Admin 조회·수정), `user_app_config` (Owner/Admin 조회 / Owner 본인 + Admin 수정).
- **스코프 내 named 문서**: 각 row는 자연키
  `(scope_type, scope_id, name)`로 식별. 한 스코프는 여러 named 문서를
  보유할 수 있고, 클라이언트는 항상 name을 명시해 호출
  (서버 측 hierarchical fall-through 없음 — §6 참고).
- **쓰기는 create / update / delete / restore로 분리 + admin/my 경로
  분리**. 동일한 네 verb를 admin 경로(`adminCreateAppConfig` 등, 모든
  스코프 대상, admin 전용, raw `AppConfig` 반환)와 self-service 경로
  (`createMyAppConfig` 등, `USER` + `current_user` 암시, 인증 유저
  본인, merged `MyAppConfig` 반환)로 대칭 노출. `create`는 엄격히 새
  row만 삽입 (같은 키에 row가 있으면 soft-deleted라도 에러), `update`
  는 기존 `ALIVE` row의 저장 JSON을 통째로 replace, `delete`는
  soft-delete (`ALIVE → DELETED`), `restore`는 delete의 명시적 역동작
  (`DELETED → ALIVE`, 값은 유지). `create` / `update` 모두 쓰기 경계
  에서 partial update / deep-merge / 키 단위 제거 없음. upsert는 없음.
  식별은 Relay `id`가 아니라 `(scope, scopeId, name)` 자연키 — my
  경로는 scope/scopeId를 서버가 주입.
- **Soft delete**: row에 `status` 컬럼 (`ALIVE` / `DELETED`)을 두고,
  record 단위 삭제는 row를 drop하지 않고 `status = DELETED`로 표시 —
  audit / undo 흐름 유지. 조회 API는 기본적으로 `ALIVE`만 노출.
- **Single source-of-truth table**: `app_configs` 한 테이블이 모든 스코프를
  보관. 노출 계층에서만 분리.
- **Relay 스타일**: Input/Payload 컨벤션, Node 인터페이스.

---

## 1. DB Layer — `app_configs` 테이블

### Schema 변경

`name`, `status` 컬럼을 추가합니다. 자연키 유니크 제약은
`(scope_type, scope_id, name)`이 됩니다.

```python
class AppConfigScopeType(enum.StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    DOMAIN_USER_DEFAULTS = "domain_user_defaults"   # 해당 도메인 사용자들에게 적용되는 기본값
    USER = "user"


class AppConfigStatus(enum.StrEnum):
    ALIVE = "alive"
    DELETED = "deleted"   # soft-deleted; audit / undo 위해 보존


@dataclass(frozen=True, slots=True)
class AppConfigKey:
    """
    단일 app_configs row의 자연키 식별자.
    `(scope_type, scope_id, name)` 트리오가 함께 파라미터로 전달되는
    모든 자리를 이 한 타입으로 교체.
    """
    scope_type: AppConfigScopeType
    scope_id: str
    name: str


class AppConfigRow(Base):
    __tablename__ = "app_configs"

    id: Mapped[uuid.UUID]

    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        StrEnumType(AppConfigScopeType, length=32), nullable=False, index=True
    )
    scope_id: Mapped[str]                     # public: 고정값 "public", 그 외: domain_name / user_id
    name: Mapped[str]                         # NEW — 설정 문서 이름 (예: "theme", "menu")

    extra_config: Mapped[dict[str, Any]]      # 유일한 payload 컬럼; 의미는 스코프별로 해석

    # NEW — soft-delete 마커. 기본 ALIVE; record-delete가 DELETED로 변경.
    status: Mapped[AppConfigStatus] = mapped_column(
        StrEnumType(AppConfigStatus, length=16),
        nullable=False,
        default=AppConfigStatus.ALIVE,
        index=True,
    )

    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]    # `modifyed_at`에서 rename

    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type", "scope_id", "name", name="uq_app_configs_scope_name"
        ),
    )
```

### Scope ID 규약

| `scope_type`            | `scope_id` 값            | `extra_config`의 의미                                |
|-------------------------|--------------------------|------------------------------------------------------|
| `public`                | 고정 문자열 `"public"`   | public(로그인 전) 스코프의 문서 값                    |
| `domain`                | `domain_name`            | 도메인 자체의 문서 값                                |
| `domain_user_defaults`  | `domain_name`            | 그 도메인 사용자들의 base 값 (per-document)          |
| `user`                  | `user_id` (UUID string)  | 사용자가 customize한 문서 값                         |

`(scope_type, scope_id, name)`에 `UniqueConstraint`가 걸려 있으므로
자연키당 단일 row 보장. 한 스코프는 임의 개수의 서로 다른 `name`을 가질
수 있습니다.

### Status 필터링

모든 read path는 기본적으로 `status = ALIVE`로 필터합니다. 호출자는
Connection의 명시적 status 필터(§3의 `AppConfigFilterGQL.status`
또는 REST 쿼리 파라미터)를 전달해 `DELETED` row도 조회 가능 —
admin recovery / audit 플로우, 또는 delete 후 name 재사용 가능 여부
확인 등에 사용. revival은 전용 `adminRestoreAppConfig` /
`restoreMyAppConfig` mutation — `status = DELETED → ALIVE`로 플립하면서
저장값은 그대로 유지. `*Create*`는 기존 row(ALIVE / DELETED 모두)가
있으면 에러, `*Update*`는 `DELETED` row에 대해 에러를 반환.

---

## 2. Repository Layer — 스코프별 분리

`models/app_config/row.py`의 `AppConfigRow`는 단일 클래스로 유지하되,
**repository는 스코프별로 4개로 분리**합니다. 권한·사용 패턴이 달라
한 클래스에 묶으면 메서드 시그니처가 비대해지기 때문입니다.

```
repositories/app_config/
├── db_source/
│   └── db_source.py         # 단일 db_source
├── public_app_config_repository.py
├── domain_app_config_repository.py
├── domain_user_defaults_app_config_repository.py
├── user_app_config_repository.py         # USER row CRUD + merged view (MyAppConfig)
└── repositories.py                       # 4개 repo 모두 노출
```

### Repository 책임 분담

| Repository                                  | 메서드                                                                                                              |
|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `PublicAppConfigRepository`                 | `get(name)`, `get_by_id(id)`, `create(name, extra_config)`, `update(name, extra_config)`, `soft_delete(name)`, `restore(name)`, `search(filter)`                                            |
| `DomainAppConfigRepository`                 | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)`, `search(domain_name, filter)` |
| `DomainUserDefaultsAppConfigRepository`     | `get(domain_name, name)`, `get_by_id(id)`, `create(domain_name, name, extra_config)`, `update(domain_name, name, extra_config)`, `soft_delete(domain_name, name)`, `restore(domain_name, name)`, `search(domain_name, filter)` |
| `UserAppConfigRepository`                   | `get(user_id, name)`, `get_by_id(id)`, `create(user_id, name, extra_config)`, `update(user_id, name, extra_config)`, `soft_delete(user_id, name)`, `restore(user_id, name)`, `search(user_id, filter)`, `get_merged(user_id, name)`, `search_merged(user_id, filter)` — 앞쪽은 `USER` row CRUD (`UserAppConfig` 서빙), 뒤쪽 두 메서드는 `AppConfigDBSource`의 merge 전용 메서드를 단일 DB 쿼리로 호출해 `DOMAIN_USER_DEFAULTS` + `USER` 두 row를 deep-merge해 반환 (`MyAppConfig` 서빙, §5). `DOMAIN` 스코프는 merge 대상이 아님. `search_merged`는 `myAppConfigs` Connection을 뒷받침 |

`DomainUserDefaultsAppConfigRepository`는 `DomainAppConfigRepository`와
동일한 호출 모양 (admin 전용)을 가지지만
`(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name)` row를
다룹니다. 분리한 이유는 "각 repository는 정확히 한 스코프와 매핑"이라는
나머지 레이아웃 원칙과 일관성을 유지하기 위함.

`UserAppConfigRepository`는 **이중 역할**: `USER` 스코프 row CRUD
(`UserAppConfig` 서빙) + merged view read (`MyAppConfig` 서빙). 다른
스코프 repository와 동일하게 `AppConfigDBSource` 하나만 주입받습니다
— user → domain_name 해소까지 포함한 merge 쿼리는 `AppConfigDBSource`
자체에 정의된 merge 전용 메서드가 단일 SQL로 처리하므로 repository
레벨에 별도의 `UserDBSource`를 두지 않습니다. merge 쿼리는
`DOMAIN_USER_DEFAULTS` + `USER` 두 row를 동일 스냅샷에서 읽어옴 (§5).
GQL 스키마는 `UserAppConfig`(raw)와 `MyAppConfig`(merged)를 별도 타입
으로 분리해 노출하지만, 내부 repository는 하나로 통합 — 별도의
`MyAppConfigRepository`를 두지 않습니다. `DOMAIN` 스코프는
admin-enforced 도메인 정책이므로 이 merge에 들어가지 않음 — 조회/수정
모두 별도 admin 경로 (`Domain.appConfigs` 등) 사용.

모든 getter / lister는 `status = ALIVE`로 필터합니다.

### `db_source`는 단일 모듈

테이블이 같으므로 ORM 쿼리 빌더는 한 군데에서 관리합니다.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get(self, key: AppConfigKey) -> AppConfigRow | None:
        async with self._db.begin_readonly_session() as db_sess:
            ...   # status = ALIVE 필터

    async def get_by_id(self, id: uuid.UUID) -> AppConfigRow | None:
        # 자연키를 row id로 이미 resolve한 Action이 사용하는 ID 기반
        # lookup (§3 "Name → ID resolve" 참고).
        async with self._db.begin_readonly_session() as db_sess:
            ...   # status = ALIVE 필터

    async def create(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # 엄격 insert. 자연키에 이미 row가 있으면(status 무관) 에러
        # (DELETED row를 되살리려면 `restore` 사용).
        async with self._db.begin_session() as db_sess:
            ...

    async def update(
        self,
        key: AppConfigKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigRow:
        # 기존 ALIVE row의 값을 extra_config로 replace.
        # 자연키에 ALIVE row가 없으면(부재 또는 DELETED) 에러.
        async with self._db.begin_session() as db_sess:
            ...

    async def soft_delete(self, key: AppConfigKey) -> AppConfigRow | None:
        # status = DELETED 설정. row가 없거나 이미 DELETED면 no-op.
        async with self._db.begin_session() as db_sess:
            ...

    async def restore(self, key: AppConfigKey) -> AppConfigRow:
        # status = ALIVE 설정, 값은 그대로 유지.
        # row가 없거나 이미 ALIVE면 에러.
        async with self._db.begin_session() as db_sess:
            ...
```

리스팅은 db_source 프리미티브가 아님 — 리스팅은 Connection 레이어의
search(filter + pagination)로 표현되고, service가 scoped-list가 아닌
별도 search 경로로 처리.

권한 체크와 스코프 검증은 service 레이어에서 수행.

---

## 3. GraphQL Schema — 엔티티별 분리 노출

### Types

각 타입은 한 스코프 안에 여러 named 문서가 있을 수 있으므로 `name`
필드를 가집니다.

```graphql
"""Public 설정 문서. 인증 없이 조회 가능."""
type PublicAppConfig implements Node {
  id: ID!

  """문서 이름 (public 스코프 안에서 unique)."""
  name: String!

  """저장된 설정 값."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""도메인 설정 문서. Admin 조회·수정. 도메인 자체의 값."""
type DomainAppConfig implements Node {
  id: ID!

  """소속 도메인 (역참조). 단순 조회만 노출."""
  domain: Domain!

  """문서 이름 (이 도메인 안에서 unique)."""
  name: String!

  """이 문서에 저장된 설정 값."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
사용자 개인 설정 문서 — 단일 `USER` 스코프 row에 대응. 본인이 저장한
raw 값만 노출 (도메인 머지 없음). 다른 스코프 타입(`PublicAppConfig`,
`DomainAppConfig`)과 동일한 형태 — `config` 한 필드만.

머지된 view (`domain_user_defaults ⊕ userCustomizedConfig`)가 필요하면
`myAppConfigs`(반환 `MyAppConfig`)를 사용 — §5 참고. `DOMAIN` 스코프
값은 머지에 참여하지 않습니다 (admin-enforced 도메인 정책).

본인 또는 Admin 조회. 본인 또는 Admin 수정.
"""
type UserAppConfig implements Node {
  id: ID!

  """소속 사용자 (역참조)."""
  user: User!

  """문서 이름 (이 사용자 안에서 unique)."""
  name: String!

  """이 문서에 저장된 raw 값 — `userCustomizedConfig`."""
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
현재 사용자 관점의 merged 앱 설정 view — `myAppConfigs`로만 접근.

같은 `name`의 두 source row
`(DOMAIN_USER_DEFAULTS, user.domain_name)`, `(USER, user.user_id)`를
deep-merge해 서빙. 둘 중 하나라도 `ALIVE`면 entry 등장. USER row가
없어도 `userCustomizedConfig`는 `{}`로 반환.

`DOMAIN` 스코프 row는 **merge에 포함되지 않음** — admin이 enforce하는
도메인 정책(사용자가 덮어쓸 수 없는 값)이므로 사용자 기본값/오버라이드와
섞이지 않고 별도 admin 전용 경로(`Domain.appConfigs` /
`adminAppConfigs` / `node(id)`)로만 노출. `UserAppConfig` /
`DomainUserDefaultsAppConfig`는 DOMAIN 정책 키를 담지 않는 것이 전제.
Admin은 `adminCreateAppConfig` / `adminUpdateAppConfig` /
`adminDeleteAppConfig`를 해당 `key.scope`로 호출해 DOMAIN 값을 관리.

Derived view지만 `Node` 구현 — refetch 편의를 위해 `(user_id, name)`
composite를 server-encoded global ID
(`base64("MyAppConfig:{user_id}:{name}")`)로 노출. `name`은 스코프
내에서만 unique하므로 user_id와 함께 묶어야 globally unique. `node(id)`
resolver는 id를 디코드한 뒤 `decoded.user_id == current_user.id` 또는
admin인 경우에만 반환 — 아니면 타인의 merge view가 노출되므로 거부.
단일 문서 조회는 `myAppConfigs` + `name` 필터 또는 `node(id)`.
"""
type MyAppConfig implements Node {
  """
  Server-encoded global ID — `base64("MyAppConfig:{user_id}:{name}")`.
  """
  id: ID!

  """문서 이름 (이 사용자 안에서 unique)."""
  name: String!

  """
  `USER` 스코프 row의 raw 값 — 사용자가 직접 저장한 값. USER row가
  없으면 `{}`.
  """
  userCustomizedConfig: JSON!

  """
  같은 `name`의
  `(scope=DOMAIN_USER_DEFAULTS, scopeId=user.domain_name)` row의
  `extra_config` raw 값 — admin이 제공한 도메인 기본값. 해당 row가
  없으면 `null`. 설정 UI에서 "도메인 제공 유저 기본값"과 "사용자 변경
  값"을 분리해 표시할 수 있게 해줌.
  """
  domainDefaultConfig: JSON

  """
  최종 적용 값: `domainDefaultConfig` ⊕ `userCustomizedConfig`의 deep
  merge (왼쪽=최저 우선, 오른쪽=최고 우선). 클라이언트는 이 값으로 UI를
  그림.
  """
  mergedConfig: JSON!

  """participating source row들의 `updatedAt` 중 최대값."""
  updatedAt: DateTime!
}
```

### 추가/확장되는 필드 (Relationship)

| 위치       | 필드                                                                                          |
|------------|-----------------------------------------------------------------------------------------------|
| `Domain`   | `appConfigs(filter, orderBy, ...pagination): DomainAppConfigConnection!`                      |
| `UserNode` | `appConfigs(filter, orderBy, ...pagination): UserAppConfigConnection!`                        |

### 권한

각 `appConfigs` child field는 부모 resolver의 권한 정책을 상속합니다 —
실제 접근 규칙은 아래 권한 매트릭스 참고.

```graphql
extend type Domain {
  """
  이 도메인이 보유한 앱 설정 문서 (DOMAIN 스코프 row).
  Admin 전용. 단일 문서 조회는 `name` 필터로. `filter.scope` /
  `filter.scopeId`는 무시됨 — 이미 이 도메인으로 고정.
  """
  appConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): DomainAppConfigConnection!
}

extend type UserNode {
  """
  이 사용자가 보유한 앱 설정 문서. 본인 또는 Admin.
  단일 문서 조회는 `name` 필터로. `filter.scope` / `filter.scopeId`는
  무시됨 — 이미 이 사용자로 고정.
  """
  appConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): UserAppConfigConnection!
}
```

자가 조회 전용 루트 필드 `myAppConfigs` (Connection)를 추가로 두어,
본인 문서를 `user_node(id)` 거치지 않고 직접 가져올 수 있도록 단축
경로를 제공합니다.

### Queries

```graphql
type Query {
  """
  Public 설정 문서 (인증 불필요). 단일 문서 조회는 `name` 필터로.
  """
  publicAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): PublicAppConfigConnection!

  """
  현재 사용자의 merged 앱 설정 view (인증 필수).
  `(DOMAIN_USER_DEFAULTS, user.domain_name)`, `(USER, user.user_id)`
  두 row를 `name`별로 deep-merge해 반환 (§5). `DOMAIN` 스코프는
  merge 대상이 아님 — 도메인 정책은 별도 admin 경로로만 노출. 단일
  문서 조회는 `name` 필터로. 필터의 `scope` / `scopeId` / `status`는
  `myAppConfigs` 문맥에서는 무시됨 — 스코프가 고정이고, merge는 `ALIVE`
  row만으로 이뤄짐.
  """
  myAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): MyAppConfigConnection!

  """
  모든 스코프의 AppConfig 통합 검색 (Admin 전용).
  필터/정렬/페이지네이션을 적용한 Relay Connection을 반환.
  """
  adminAppConfigs(
    filter: AppConfigFilterGQL = null
    orderBy: [AppConfigOrderByGQL!] = null
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
    limit: Int = null
    offset: Int = null
  ): AppConfigConnection!

  # ─ 아래는 신규 추가가 아니라 기존 루트 필드 활용 ─
  #
  # user_node(id: String!): UserNode
  #                                — Admin 전용 → user_node(id: ...) { appConfigs { ... } }
  # domain(name: String!): Domain  — Admin 전용 → domain(name: ...) { appConfigs { ... } }
  # node(id: ID!): Node            — Relay 표준 → 어느 AppConfig든 ID로 직접 접근
}
```

#### Connection / Filter / OrderBy

Filter / orderBy 타입은 통합 — `AppConfigFilterGQL`과
`AppConfigOrderByGQL` 한 쌍을 모든 Connection (admin cross-scope +
typed)이 공유합니다. Connection 자체는 스코프별 typed 형태를 유지해
`node` payload가 알맞은 구체 타입을 보유하도록 합니다.

```graphql
# ── Connections (typed per scope) ─────────────────────────────

"""모든 스코프의 AppConfig를 담는 Relay Connection."""
type AppConfigConnection {
  edges: [AppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type AppConfigEdge {
  cursor: String!
  node: AppConfig!
}

type PublicAppConfigConnection {
  edges: [PublicAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type PublicAppConfigEdge {
  cursor: String!
  node: PublicAppConfig!
}

type DomainAppConfigConnection {
  edges: [DomainAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type DomainAppConfigEdge {
  cursor: String!
  node: DomainAppConfig!
}

type UserAppConfigConnection {
  edges: [UserAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type UserAppConfigEdge {
  cursor: String!
  node: UserAppConfig!
}

"""현재 사용자의 merged view를 담는 Relay Connection (`myAppConfigs` 전용)."""
type MyAppConfigConnection {
  edges: [MyAppConfigEdge!]!
  pageInfo: PageInfo!
  count: Int!
}
type MyAppConfigEdge {
  cursor: String!
  node: MyAppConfig!
}

# ── Filter / OrderBy (모든 Connection 공용) ───────────────────

"""
AppConfig 검색 필터. 최상위 scalar 필드는 AND로 결합. 임의의 불리언
조합이 필요하면 `AND` / `OR` / `NOT` 아래에 predicate를 중첩.
"""
input AppConfigFilterGQL {
  """
  스코프 타입 필터. `adminAppConfigs`에서만 의미가 있고, per-scope
  Connection (`publicAppConfigs`, `Domain.appConfigs`,
  `UserNode.appConfigs`, `myAppConfigs`)에서는
  이미 필드 자체가 스코프를 고정하므로 무시됩니다.
  """
  scope: AppConfigScopeEnumFilter = null

  """
  `scope_id` exact match. `scope`와 동일한 제약 — per-scope
  Connection에서는 `scope_id`가 함의되어 있어 무시됩니다.
  """
  scopeId: StringFilter = null

  """문서 `name` 필터."""
  name: StringFilter = null

  """생성 시각 범위 필터."""
  createdAt: DateTimeFilter = null

  """수정 시각 범위 필터."""
  updatedAt: DateTimeFilter = null

  """
  row `status` 필터. 생략 시 Connection은 `ALIVE` row만 반환.
  `{ equals: DELETED }` (또는 `{ in: [ALIVE, DELETED] }`)를 전달하면
  soft-deleted row도 포함 — admin recovery / audit 플로우와,
  delete 후 name 재사용 여부 확인 등에 사용.
  """
  status: AppConfigStatusEnumFilter = null

  """모든 sub-filter가 일치해야 함 (AND)."""
  AND: [AppConfigFilterGQL!] = null

  """최소 하나의 sub-filter가 일치해야 함 (OR)."""
  OR: [AppConfigFilterGQL!] = null

  """어느 sub-filter도 일치하지 않아야 함 (NOT)."""
  NOT: [AppConfigFilterGQL!] = null
}

"""AppConfigScopeGQL용 EnumFilter (equals / in / not_equals / not_in)."""
input AppConfigScopeEnumFilter {
  equals: AppConfigScopeGQL
  in: [AppConfigScopeGQL!]
  notEquals: AppConfigScopeGQL
  notIn: [AppConfigScopeGQL!]
}

"""AppConfigStatusGQL용 EnumFilter (equals / in / not_equals / not_in)."""
input AppConfigStatusEnumFilter {
  equals: AppConfigStatusGQL
  in: [AppConfigStatusGQL!]
  notEquals: AppConfigStatusGQL
  notIn: [AppConfigStatusGQL!]
}

input AppConfigOrderByGQL {
  field: AppConfigOrderField!
  direction: OrderDirection! = ASC
}

"""
`SCOPE` / `SCOPE_ID`는 `adminAppConfigs`에서만 유용하고, per-scope
Connection에서는 상수로 축퇴되어 효과가 없습니다.
"""
enum AppConfigOrderField {
  SCOPE
  SCOPE_ID
  NAME
  UPDATED_AT
  CREATED_AT
}
```

모든 Connection은 기본적으로 `status = ALIVE`로 필터됩니다. 호출자가
`filter.status`를 명시하면 `DELETED` row(또는 양쪽 모두)도 조회
가능 — admin recovery / audit 플로우가 이 방식으로 deleted row를
읽습니다.

### Mutations

쓰기는 **admin 경로**와 **self-service(`my`) 경로**로 분리된 총 8개
mutation으로 표현합니다.

- `admin*AppConfig` (4개): `AppConfigKey { scope, scopeId, name }`를
  입력으로 받아 모든 스코프를 커버. **admin 전용**. 응답은 raw
  `AppConfig`.
- `*MyAppConfig` (4개): 스코프 `USER` + `scopeId = current_user.user_id`
  를 암시. 입력은 `name` (+ write 계열의 경우 `config`)만. 인증된
  유저 누구든 본인 문서에 대해 호출 가능. 응답은 **merged `MyAppConfig`** —
  한 번의 round-trip으로 최신 merge view를 획득.

스코프별 분기는 **내부 구현**에만 존재 — 쿼리는 타입 편의성을 위해
나뉘어 있고(`Domain.appConfigs`, `UserNode.appConfigs`, `myAppConfigs`,
`publicAppConfigs`, `adminAppConfigs`), §2의 repository 분할이 쓰기를
적절한 백엔드로 라우팅합니다. 권한 검사는 **service 레이어**에서
수행 (아래 권한 매트릭스 참조).

```graphql
type Mutation {
  # ── Admin 경로 — 모든 스코프, admin 전용 ──────────────────────

  """
  새 앱 설정 문서를 생성 (admin 전용). `AppConfigKey { scope, scopeId,
  name }`로 식별. 엄격 insert — 같은 자연키에 row가 있으면 `status`
  관계 없이 에러 (soft-deleted 복구는 `adminRestoreAppConfig`).

  `USER` 스코프에 대해 admin이 대신 seed할 때도 이 mutation 사용.
  응답은 raw `AppConfig` — 대상 사용자 관점의 merged view는 해당 유저
  세션이 `myAppConfigs`를 재조회하면 반영됨.
  """
  adminCreateAppConfig(input: AdminCreateAppConfigInput!): AdminCreateAppConfigPayload!

  """
  기존 앱 설정 문서의 저장 JSON을 입력으로 통째로 replace (admin 전용).
  자연키에 `ALIVE` row가 없으면(부재 또는 `DELETED`) 에러.
  """
  adminUpdateAppConfig(input: AdminUpdateAppConfigInput!): AdminUpdateAppConfigPayload!

  """
  앱 설정 문서를 soft-delete (`status = DELETED`, admin 전용). row는
  audit용으로 유지되며 같은 `key`로 `adminRestoreAppConfig`를 호출해
  되살릴 수 있음. Idempotent — row가 없거나 이미 `DELETED`이면 silent
  no-op.
  """
  adminDeleteAppConfig(input: AdminDeleteAppConfigInput!): AdminDeleteAppConfigPayload!

  """
  soft-deleted 앱 설정 문서를 복구 (`status = DELETED → ALIVE`, admin
  전용). 저장 값은 그대로 유지 — 값을 바꾸려면 이어서
  `adminUpdateAppConfig` 호출. row가 없거나 이미 `ALIVE`이면 에러.
  """
  adminRestoreAppConfig(input: AdminRestoreAppConfigInput!): AdminRestoreAppConfigPayload!

  # ── Self-service (my) 경로 — USER + current_user 암시 ─────────

  """
  현재 사용자의 `USER` 스코프 문서를 생성 (인증 필수). 입력의 `name` +
  암묵적 `scopeId = current_user.user_id`로 `userCustomizedConfig`를
  새로 저장. 엄격 insert — 같은 `name`에 `ALIVE` / `DELETED` USER row
  가 이미 있으면 에러 (복구는 `restoreMyAppConfig`).

  응답은 재계산된 `MyAppConfig` — `DOMAIN_USER_DEFAULTS`와 2-way
  merge한 view를 한 번에 돌려줌.
  """
  createMyAppConfig(input: CreateMyAppConfigInput!): CreateMyAppConfigPayload!

  """
  현재 사용자의 `USER` 스코프 문서를 replace (인증 필수). 해당 `name`
  의 `ALIVE` USER row가 없으면 에러. 응답은 재계산된 `MyAppConfig`.
  """
  updateMyAppConfig(input: UpdateMyAppConfigInput!): UpdateMyAppConfigPayload!

  """
  현재 사용자의 `USER` 스코프 문서를 soft-delete (인증 필수). 해당
  `name`의 USER row가 `DELETED`로 전환. Idempotent. 응답은 delete
  이후 재계산된 `MyAppConfig` — 남아있는 `DOMAIN_USER_DEFAULTS`만
  반영. 해당 `name`에 ALIVE source가 전부 사라지면 `null`.
  """
  deleteMyAppConfig(input: DeleteMyAppConfigInput!): DeleteMyAppConfigPayload!

  """
  현재 사용자의 soft-deleted USER 문서를 복구 (`DELETED → ALIVE`).
  저장 값은 그대로 유지 — 값을 바꾸려면 이어서 `updateMyAppConfig`
  호출. row가 없거나 이미 `ALIVE`이면 에러. 응답은 재계산된
  `MyAppConfig`.
  """
  restoreMyAppConfig(input: RestoreMyAppConfigInput!): RestoreMyAppConfigPayload!
}

enum AppConfigScopeGQL {
  PUBLIC
  DOMAIN
  DOMAIN_USER_DEFAULTS
  USER
}

enum AppConfigStatusGQL {
  ALIVE
  DELETED
}

# ── 쓰기 mutation 공용 식별자 ──────────────────────────────────

"""
단일 app config row를 식별하는 자연키 composite.
Repository / db_source 레이어의 Python `AppConfigKey` dataclass와
동일한 식별 모델을 GQL 입력으로 노출.
- `PUBLIC`:               `scopeId`는 고정 문자열 `"public"`.
- `DOMAIN`:               `scopeId`는 `domain_name`.
- `DOMAIN_USER_DEFAULTS`: `scopeId`는 `domain_name`.
- `USER`:                 `scopeId`는 `user_id` (UUID string).
- `name`은 문서 이름 (스코프 안에서 unique).
"""
input AppConfigKey {
  scope: AppConfigScopeGQL!
  scopeId: String!
  name: String!
}

# ── Admin 입력 ────────────────────────────────────────────────

input AdminCreateAppConfigInput {
  """대상 row 식별자."""
  key: AppConfigKey!

  """
  초기 저장 값 — 비어있는 문서로 생성하려면 `{}` 전달.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: 문서의 `config`로 저장.
  - `USER`: 해당 사용자의 `userCustomizedConfig`로 저장.
  """
  config: JSON!
}

input AdminUpdateAppConfigInput {
  """대상 row 식별자."""
  key: AppConfigKey!

  """
  새 저장 값 — row 내용을 통째로 replace. 문서를 비우고 row만 유지하려면
  `{}` 전달.
  - `PUBLIC` / `DOMAIN` / `DOMAIN_USER_DEFAULTS`: 해당 문서의 `config`를
    직접 replace.
  - `USER`: 해당 사용자의 `userCustomizedConfig`를 replace (병합 결과
    `MyAppConfig.mergedConfig`는 read-only computed이므로 직접 쓸 수 없음).
  """
  config: JSON!
}

input AdminDeleteAppConfigInput {
  """대상 row 식별자."""
  key: AppConfigKey!
}

input AdminRestoreAppConfigInput {
  """대상 row 식별자."""
  key: AppConfigKey!
}

# ── My 입력 — scope=USER, scopeId=current_user.user_id 암시 ──

input CreateMyAppConfigInput {
  """문서 이름 (현재 사용자 안에서 unique)."""
  name: String!

  """
  초기 `userCustomizedConfig` 값 — 비어있는 문서로 생성하려면 `{}`.
  `MyAppConfig.mergedConfig`는 read-only computed이므로 직접 쓸 수 없음.
  """
  config: JSON!
}

input UpdateMyAppConfigInput {
  """대상 문서 이름."""
  name: String!

  """새 `userCustomizedConfig` 값 — 통째로 replace."""
  config: JSON!
}

input DeleteMyAppConfigInput {
  """대상 문서 이름."""
  name: String!
}

input RestoreMyAppConfigInput {
  """대상 문서 이름."""
  name: String!
}

# ── Admin Payload — raw AppConfig 반환 ───────────────────────

"""
`adminCreateAppConfig` 결과. 새로 생성된 row를 generic `AppConfig`로
노출. 대상 사용자 관점의 merged view는 해당 유저 세션이
`myAppConfigs`를 재조회하면 반영됨.
"""
type AdminCreateAppConfigPayload {
  appConfig: AppConfig!
}

"""
`adminUpdateAppConfig` 결과. 영향 받은 row를 스코프에 상관없이 generic
`AppConfig`로 노출 — `AppConfig.config`는 raw 저장 값만 담고 있음.
특정 사용자의 raw USER row는 `UserNode.appConfigs`(반환
`UserAppConfig`)로 조회.
"""
type AdminUpdateAppConfigPayload {
  appConfig: AppConfig!
}

"""
`adminDeleteAppConfig` 결과. 반환된 row는 soft-delete 후 상태
(`status = DELETED`)를 반영.
"""
type AdminDeleteAppConfigPayload {
  appConfig: AppConfig!
}

"""
`adminRestoreAppConfig` 결과. 반환된 row는 복구 후 상태
(`status = ALIVE`, 저장값 불변)를 반영.
"""
type AdminRestoreAppConfigPayload {
  appConfig: AppConfig!
}

# ── My Payload — merged MyAppConfig 반환 ─────────────────────

"""`createMyAppConfig` 결과. 쓴 직후의 재계산된 `MyAppConfig`."""
type CreateMyAppConfigPayload {
  myAppConfig: MyAppConfig!
}

"""`updateMyAppConfig` 결과. 쓴 직후의 재계산된 `MyAppConfig`."""
type UpdateMyAppConfigPayload {
  myAppConfig: MyAppConfig!
}

"""
`deleteMyAppConfig` 결과. 해당 `name`에 남아있는 merge source
(`DOMAIN_USER_DEFAULTS`)만으로 재계산된 `MyAppConfig`. USER row가
사라진 뒤 해당 `name`에 어떤 ALIVE source도 없으면 `null`.
"""
type DeleteMyAppConfigPayload {
  myAppConfig: MyAppConfig
}

"""`restoreMyAppConfig` 결과. 복구 후 재계산된 `MyAppConfig`."""
type RestoreMyAppConfigPayload {
  myAppConfig: MyAppConfig!
}

"""Admin mutation 응답용 범용 AppConfig 타입 — raw 저장 값을 그대로 노출."""
type AppConfig implements Node {
  id: ID!
  scope: AppConfigScopeGQL!
  scopeId: String!
  name: String!
  status: AppConfigStatusGQL!

  """
  저장된 raw 값 (`extra_config`). USER 스코프에서는 사용자 customized
  값이며 merge된 결과가 아님.
  """
  config: JSON!

  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### 권한 매트릭스

쿼리:

| 작업                     | Anonymous | User       | Admin  |
|--------------------------|-----------|------------|--------|
| `publicAppConfigs`       | ✅        | ✅         | ✅     |
| `myAppConfigs`           | ❌        | ✅ (본인)  | ✅     |
| `adminAppConfigs`        | ❌        | ❌         | ✅     |
| `Domain.appConfigs`      | ❌        | ❌         | ✅     |
| `UserNode.appConfigs`    | ❌        | ✅ (본인)  | ✅     |

쓰기 mutation은 admin / my 두 경로로 분리되어 있으며 각각 별도
규칙이 적용됩니다.

**Admin 경로** — `input.key.scope`와 무관하게 admin 전용
(`adminCreateAppConfig`, `adminUpdateAppConfig`, `adminDeleteAppConfig`,
`adminRestoreAppConfig`):

| 작업                 | Anonymous | User | Admin |
|----------------------|-----------|------|-------|
| `admin*AppConfig`    | ❌        | ❌   | ✅    |

**Self-service (my) 경로** — `scope=USER` + `scopeId=current_user.user_id`
암시 (`createMyAppConfig`, `updateMyAppConfig`, `deleteMyAppConfig`,
`restoreMyAppConfig`):

| 작업                 | Anonymous | 인증 유저 (본인) | Admin (본인) |
|----------------------|-----------|------------------|--------------|
| `*MyAppConfig`       | ❌        | ✅               | ✅           |

> Admin이 다른 사용자의 `USER` row를 건드릴 때는 my 경로가 아니라
> admin 경로로 `AppConfigKey { scope: USER, scopeId: target_user_id,
> name }`를 명시해 호출.

권한 체크 위치:
- Admin 경로 resolver: service 레이어에서 `check_admin_only()` 후
  `input.key.scope`로 §2의 해당 repository로 라우팅. `scopeId`를
  silently 재해석하지 않음 — 비-admin은 거부.
- My 경로 resolver: service 레이어에서 익명 호출 거부 후 `current_user`
  를 resolve해 `UserAppConfigRepository.{create|update|soft_delete|
  restore}`에 직접 전달 — `scopeId`는 입력에 없고 서버가 주입.
- `Domain.appConfigs` field resolver: `check_admin_only()`로 admin이
  아닌 요청에는 빈 Connection 반환.
- `UserNode.appConfigs` field resolver: 부모 노드의 `user_id`가
  `current_user`와 다르고 admin도 아니면 빈 Connection 반환.

#### Name → ID resolve와 ID 기반 Action

search / update / mutate를 구현하는 Action들은 내부적으로 모두 **row
`id`** 기반으로 동작합니다 — 자연키를 직접 들고 돌아다니지 않음.
resolve는 RBAC 체크 바로 앞 단계의 service 레이어 작업:

1. 자연키 `(scope, scopeId, name)` → row `id`를 해당 repository로
   조회. 이 조회는 **권한 무관** — 자연키만 있으면 누구든 호출 가능.
   호출자가 접근 불가능한 row의 `id`를 돌려줘도 무방 (다음 단계에서
   막힘).
2. 해석된 `id`를 기준으로 RBAC 체크(표준 RBAC plumbing이 scope +
   actor context를 소비).
3. ID 기반 Action(search, update, delete, restore 등)을 repository로
   dispatch.

덕분에 Action 자체는 ID-only로 균일하게 유지되고, API surface에서는
자연키 식별을 계속 받을 수 있음 — 클라이언트는 row ID를 알 필요 없음.

---

## 4. REST Schema — `/v2/app-configs/...`

기존 `app-configs` prefix
(`api/rest/v2/app_config/registry.py`의
`RouteRegistry.create("app-configs", ...)`) 아래에 마운트 —
`api/rest/v2/CLAUDE.md`의 v2 컨벤션과 정합.

### Endpoints

모든 스코프-파라미터화 엔드포인트는 단일 URL 형태를 따릅니다:
`/v2/app-configs/{scope_type}/{scope_id}[/{name}]`. 여기서

- `{scope_type}` ∈ `public | domain | domain_user_defaults | user`
  (§1의 `AppConfigScopeType`).
- `{scope_id}`는 §1 Scope ID 규약 — `public`은 고정 문자열
  `"public"`, `domain` / `domain_user_defaults`는 `domain_name`,
  `user`는 `user_id` (UUID).
- `{name}`은 문서 이름.

verb는 GQL mutation과 1:1 매핑:

| Method | Path                                                     | 설명                                                    |
|--------|----------------------------------------------------------|---------------------------------------------------------|
| GET    | `/v2/app-configs/{scope_type}/{scope_id}`                | 스코프 내 문서 목록 (기본 `status=ALIVE` 필터)           |
| GET    | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | 단일 문서 조회                                           |
| POST   | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | create (엄격 insert; row가 있으면 `409`)                |
| PUT    | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | replace (ALIVE row 없으면 `404`)                        |
| DELETE | `/v2/app-configs/{scope_type}/{scope_id}/{name}`         | soft-delete                                             |
| POST   | `/v2/app-configs/{scope_type}/{scope_id}/{name}/restore` | restore (`DELETED → ALIVE`, 값 불변)                    |

권한은 §3의 permission matrix와 `input.key.scope` 표 그대로 — 익명
read는 `scope_type=public` read에만 허용, 비-`user` 스코프 쓰기는
admin 전용, `scope_type=user` 쓰기는 admin 또는 본인
(`{scope_id} == current_user.user_id`).

스코프-파라미터화 형태를 벗어난 shortcut 엔드포인트:

| Method | Path                                | 권한   | 설명                                          |
|--------|-------------------------------------|--------|-----------------------------------------------|
| GET    | `/v2/app-configs/my[/{name}]`       | User   | 본인 문서 목록/단일 조회 (병합 결과 포함)     |
| POST   | `/v2/app-configs/my/{name}`         | User   | 본인 문서 생성                                |
| PUT    | `/v2/app-configs/my/{name}`         | User   | 본인 문서 replace                             |
| DELETE | `/v2/app-configs/my/{name}`         | User   | 본인 문서 soft-delete                         |
| POST   | `/v2/app-configs/my/{name}/restore` | User   | 본인의 soft-deleted 문서 복구                 |
| POST   | `/v2/app-configs/search`            | Admin  | 모든 스코프 통합 검색 (body는 `adminAppConfigs`와 동일 스키마) |

`POST /v2/app-configs/search`는 GQL `adminAppConfigs`와 동일한 입력
스키마(`filter` / `orderBy` / 페이지네이션 인자)를 body로 받아 동일한
결과를 반환합니다.

> `/v2/app-configs/my/...`는 컨벤션상 `my_` self-service 패턴
> (`api/rest/v2/CLAUDE.md`) — adapter가 내부에서 `current_user()`를
> 해석해 `scope_id`를 본인의 `user_id`로 고정합니다. PUT body는
> `userCustomizedConfig`(REST에서는 snake_case로
> `user_customized_config`)만 받습니다 — 다른 사용자를 가리킬 입력
> 필드 자체가 없음.

> 조회 endpoint는 기본적으로 `status = ALIVE`만 반환. revival은 전용
> `POST {path}/restore` 액션 — soft-deleted 자연키에 `PUT`/`POST`
> 하면 revive하지 않고 에러(PUT은 `ALIVE` row 부재로 `404`, POST는
> 이미 row 존재로 `409`).

---

## 5. `MyAppConfig` — Merge 정책

> 여기 설명하는 머지 시맨틱은 **`MyAppConfig` (= `myAppConfigs` 반환
> 타입)에만** 적용됩니다. `PublicAppConfig` / `DomainAppConfig` /
> `UserAppConfig` (raw USER row view)는 교차-스코프 머지 없이 raw
> `extra_config` 그대로 `config` 한 필드로 읽혀 나가고,
> `mergedConfig` / `domainDefaultConfig` 같은 부가 view도 없음.
> `DOMAIN` 스코프 값은 admin-only 정책이며 **merge 대상이 아님** —
> 별도 admin 경로로만 노출.

### 저장

- `user_app_config`의 `extra_config`(DB 컬럼) = `UserAppConfig.config`
  = `MyAppConfig.userCustomizedConfig`는 named 문서 단위로 **사용자가
  직접 지정한 값만** 저장.
- 머지의 도메인-측 입력은
  `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=domain_name, name=N)`
  row 하나 — admin이 제공하는 유저 기본값. 사용자 행에 복사하지
  않음 — admin이 기본값을 바꿨을 때 모든 사용자 행을 갱신해야 하는
  문제를 피하기 위함.
- `DOMAIN` 스코프 row는 admin-enforced 정책이며 **merge에 참여하지
  않음** — 사용자가 덮어쓸 수 없는 값이므로 `DOMAIN_USER_DEFAULTS`
  / `USER`와 섞으면 안 됨. 전제: `UserAppConfig` /
  `DomainUserDefaultsAppConfig`는 DOMAIN 정책 키를 담지 않음. 관리
  / 노출은 전적으로 별도 admin 경로(`Domain.appConfigs` /
  `adminAppConfigs`)에서.
- 도메인-측 값은 **`name`별로 적용**: 같은 `name`의
  `DOMAIN_USER_DEFAULTS` row가 같은 `name`의 `USER` row의
  `userCustomizedConfig`의 merge base. 서로 다른 `name`은 독립적.

### 조회 (Merge)

Merge는 `UserAppConfigRepository`가 전담하며, DB 접근은 `AppConfigDBSource`
의 merge 전용 메서드 한 번으로 끝냅니다 — **단일 쿼리**로
`DOMAIN_USER_DEFAULTS` + `USER` 두 row를 동일 스냅샷에서 읽어옵니다.
자연키 `UniqueConstraint` 덕분에 최대 2 row로 bounded. 주어진
`(user_id, name)`에 대해:

1. `AppConfigDBSource.get_user_merged_config(user_id, name)` 호출 —
   단일 SQL이 `users` 서브쿼리로 `domain_name`을 해소하면서 `app_configs`
   에서 두 source row를 함께 읽어옴:
   - `(scope_type=DOMAIN_USER_DEFAULTS, scope_id=user의 domain_name, name=name)`
     → 유저 기본값.
   - `(scope_type=USER, scope_id=user_id, name=name)` → 사용자
     customized 값.
2. 읽어온 row들로 **deep merge** (낮은 → 높은 우선):
   `domain_user_defaults ⊕ userCustomizedConfig`. 중첩 객체는 키
   단위로 재귀 병합하고, 같은 leaf 키에서는 우선순위가 높은 값이
   이깁니다. 리스트는 leaf로 간주해 우선순위가 높은 값으로 통째로
   대체 (요소 단위 merge는 의미가 모호하므로). 결과는
   `MyAppConfig.mergedConfig`로 노출되고, 각 source row의 raw
   `extra_config`는 `MyAppConfig.domainDefaultConfig` /
   `MyAppConfig.userCustomizedConfig`로 노출.
   `MyAppConfig.updatedAt`은 참여 row들의 `updatedAt` 중 최대값.

두 row가 한 readonly 트랜잭션에서 함께 읽히므로 관리자 쓰기 중간에
끼어든 반쪽 상태를 보는 일은 없습니다.

`DOMAIN` 스코프 row는 이 merge에 참여하지 않습니다 — admin-enforced
도메인 정책이므로 사용자 기본값/오버라이드와 섞이지 않고, 관리/조회
모두 별도 admin 경로(`Domain.appConfigs` / `adminAppConfigs` /
`node(id)`)로만 이뤄집니다. 따라서 `UserAppConfigRepository`는 DOMAIN
row를 전혀 읽지 않고, 비-admin 유저가 이 merge 경로로 DOMAIN 내용을
엿볼 수 없습니다.

> merge 시 `DOMAIN_USER_DEFAULTS` row 읽기는 `AppConfigDBSource`가
> 단일 SQL에서 `users` 서브쿼리로 호출자의 `domain_name`을 해소한 뒤
> 수행 — admin 경로를 거치지 않으며 권한 우회도 아님. 유저는 자기
> 도메인의 기본값만, merge 경로로만 읽을 수 있음.

Connection 쿼리(`myAppConfigs`)는 `AppConfigDBSource`의 search 전용
메서드가 백업 — 필터/페이지네이션을 SQL에 반영한 단일 쿼리로 두 스코프
(`DOMAIN_USER_DEFAULTS`, `USER`)의 `ALIVE` row를 `name`별로 묶어
merge 결과를 1건씩 반환. 둘 중 적어도 하나가 해당 `name`에 존재하는
모든 문서가 entry로 등장.

```python
class AppConfigDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_user_merged_config(
        self, user_id: str, name: str
    ) -> MergedAppConfig:
        # 단일 SQL로 `users` 서브쿼리에서 domain_name을 해소하면서
        # app_configs의 두 source row(DOMAIN_USER_DEFAULTS = user의
        # domain_name, USER = user_id)를 함께 조회 — 자연키
        # UniqueConstraint 덕분에 최대 2 row로 bounded. DOMAIN 스코프는
        # admin-only 정책이라 이 merge에 포함하지 않음.
        user_domain_sq = (
            sa.select(UserRow.domain_name)
            .where(UserRow.id == sa.cast(user_id, sa.UUID))
            .scalar_subquery()
        )
        async with self._db.begin_readonly_session() as db_sess:
            rows = (await db_sess.execute(
                sa.select(AppConfigRow).where(
                    AppConfigRow.status == AppConfigStatus.ALIVE,
                    AppConfigRow.name == name,
                    sa.or_(
                        sa.and_(
                            AppConfigRow.scope_type
                                == AppConfigScopeType.DOMAIN_USER_DEFAULTS,
                            AppConfigRow.scope_id == user_domain_sq,
                        ),
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.USER,
                            AppConfigRow.scope_id == user_id,
                        ),
                    ),
                )
            )).scalars().all()

        by_scope = {row.scope_type: row for row in rows}
        domain_defaults_row = by_scope.get(AppConfigScopeType.DOMAIN_USER_DEFAULTS)
        user_row = by_scope.get(AppConfigScopeType.USER)

        domain_defaults = domain_defaults_row.extra_config if domain_defaults_row else None
        user_customized = user_row.extra_config if user_row else {}

        return MergedAppConfig(
            user_id=user_id,
            name=name,
            user_customized_config=user_customized,                 # MyAppConfig.userCustomizedConfig
            domain_default_config=domain_defaults,                  # MyAppConfig.domainDefaultConfig
            merged_config=deep_merge(                               # MyAppConfig.mergedConfig
                domain_defaults or {},
                user_customized,
            ),
            updated_at=max_updated_at([domain_defaults_row, user_row]),
        )

    async def search_user_merged_configs(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> MergedAppConfigPage:
        # 단일 SQL로 users 서브쿼리에서 domain_name 해소 + 두 스코프
        # (DOMAIN_USER_DEFAULTS, USER)의 ALIVE row를 가져와
        # (`get_user_merged_config`와 동일한 WHERE 조건에서 name 필터 →
        # `filter`로 일반화) name별로 묶어 merge. 페이지네이션은
        # `(name, updated_at)` 안정 키 기준으로 cursor를 정의해 SQL에
        # 반영. 구현 상세는 §3 Connection 리졸버에서.
        ...


class UserAppConfigRepository:
    """
    `USER` 스코프 row CRUD (`UserAppConfig` 서빙) + merged view read
    (`MyAppConfig` 서빙)을 함께 담당. merge 경로는 `AppConfigDBSource`의
    merge 전용 메서드 단일 쿼리로 두 source row를 읽어 MergedAppConfig를
    반환하며 `DOMAIN` 스코프는 건드리지 않음. 별도의
    `MyAppConfigRepository`는 두지 않고 이 repository 하나로 통합.
    """

    _db_source: AppConfigDBSource

    def __init__(self, db_source: AppConfigDBSource) -> None:
        self._db_source = db_source

    # ── USER row CRUD (UserAppConfig) ─────────────────────────────

    async def get(self, user_id: str, name: str) -> AppConfigRow | None:
        return await self._db_source.get(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def get_by_id(self, id: uuid.UUID) -> AppConfigRow | None:
        return await self._db_source.get_by_id(id)

    async def create(
        self, user_id: str, name: str, extra_config: Mapping[str, Any]
    ) -> AppConfigRow:
        return await self._db_source.create(
            AppConfigKey(AppConfigScopeType.USER, user_id, name),
            extra_config,
        )

    async def update(
        self, user_id: str, name: str, extra_config: Mapping[str, Any]
    ) -> AppConfigRow:
        return await self._db_source.update(
            AppConfigKey(AppConfigScopeType.USER, user_id, name),
            extra_config,
        )

    async def soft_delete(self, user_id: str, name: str) -> AppConfigRow | None:
        return await self._db_source.soft_delete(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def restore(self, user_id: str, name: str) -> AppConfigRow:
        return await self._db_source.restore(
            AppConfigKey(AppConfigScopeType.USER, user_id, name)
        )

    async def search(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> AppConfigPage:
        # scope=USER + scope_id=user_id로 바인딩한 raw USER row 검색.
        return await self._db_source.search(
            scope_type=AppConfigScopeType.USER,
            scope_id=user_id,
            filter=filter,
            pagination=pagination,
        )

    # ── Merged view (MyAppConfig) ─────────────────────────────────
    # `AppConfigDBSource`의 merge 전용 메서드가 users 서브쿼리로
    # domain_name 해소까지 단일 SQL에서 처리하므로 repository는 thin
    # 위임.

    async def get_merged(self, user_id: str, name: str) -> MergedAppConfig:
        return await self._db_source.get_user_merged_config(user_id, name)

    async def search_merged(
        self,
        user_id: str,
        filter: AppConfigFilter,
        pagination: Pagination,
    ) -> MergedAppConfigPage:
        return await self._db_source.search_user_merged_configs(
            user_id, filter, pagination
        )
```

### 노출

`MyAppConfig`는 같은 논리 문서를 세 가지 view로 노출 — WebUI가
렌더링·편집을 깔끔하게 처리할 수 있도록:

- `userCustomizedConfig` — 사용자가 직접 set한 raw 값 (USER row가
  없으면 `{}`)
- `domainDefaultConfig` — 같은 `name`의 `DOMAIN_USER_DEFAULTS` row의
  raw `extra_config` — admin이 제공하는 도메인 기본값 (row 없으면
  `null`)
- `mergedConfig` — `domainDefaultConfig ⊕ userCustomizedConfig`, UI가
  실제로 적용하는 값

REST `GET /v2/app-configs/my/{name}` 응답도 같은 세 view를 가짐
(snake_case: `user_customized_config`, `domain_default_config`,
`merged_config`).

`DOMAIN` 스코프 row는 이 view에 포함되지 않음 — admin이 관리/조회하는
별도 스코프(`Domain.appConfigs` / `adminAppConfigs` / REST
`/v2/app-configs/domain/...`)로만 노출.

---

## 6. Client Integration — WebUI 부트스트랩

WebUI는 항상 `(scope, scopeId, name)`을 명시해 config를 요청합니다.
로그인 전 로드할 public 문서 목록은 **프론트엔드가 전담**(WebUI
번들에 하드코드/포함) — 서버는 부트스트랩 리스트를 제공하지 않음.

### 부트스트랩 흐름

1. **로그인 전 (anonymous)** — WebUI가 필요한 각 public 문서에 대해
   `name` 필터를 건 `publicAppConfigs` 쿼리를 발행 (인증 없음).
   `theme` / `branding` 등은 단일 문서 조회 형태 — §7 S1 참고. edge가
   없거나 네트워크 에러 시 해당 문서에 대해 WebUI 내장 기본값으로
   fallback.

2. **로그인 후** — WebUI가 `myAppConfigs` 쿼리를 1회 발행해 호출자의
   *모든* user 문서를 가져옴. 각 항목은 `userCustomizedConfig`,
   `domainDefaultConfig`와 2-way merge된 `mergedConfig`를 포함
   (§5 참고). DOMAIN 스코프(admin-enforced 정책)는 이 merge에 포함되지
   않으므로, admin UI가 도메인 정책을 보려면 `Domain.appConfigs` /
   `adminAppConfigs`를 별도로 조회. §7 S2 참고.

---

## 7. User Scenarios — 호출자 관점의 end-to-end 흐름

각 시나리오는 "누가 / 언제 / 무엇을 하고 싶은가"와 실제 호출 스펙을
함께 보여줍니다. 클라이언트 구현 시의 참조 포인트.

### S1. 로그인 전 public 설정 로딩 (Anonymous)

WebUI가 로그인 화면을 그리기 전에 public `theme` 문서를 로딩.
(`config` JSON 내부 구조는 프론트엔드가 소유 — 백엔드는 opaque하게 저장.)

```graphql
query LoadPublicTheme {
  publicAppConfigs(filter: { name: { equals: "theme" } }) {
    edges { node { name config updatedAt } }
  }
}
```

- 인증 토큰 없음.
- 단일 문서 조회는 Connection에 `name` 필터를 거는 형태 — 단수 root
  필드는 두지 않음.
- 실패해도 (edge 없음, 네트워크 에러) WebUI는 내장 기본값으로 fallback.
  로그인 전 문서 세트는 WebUI에 하드코드 (§6 참고).

### S2. 로그인 직후 사용자 부트스트랩

WebUI가 로그인 성공 시 "이 사용자에게 보여줄 모든 문서"를 한 번에 확보 —
호출자의 모든 named 문서.

```graphql
query BootstrapMe {
  myAppConfigs {
    edges {
      node {
        name
        userCustomizedConfig
        domainDefaultConfig
        mergedConfig
        updatedAt
      }
    }
  }
  publicAppConfigs {
    edges { node { name config } }
  }
}
```

- 서버: `myAppConfigs`는 두 source row(`USER`,
  `DOMAIN_USER_DEFAULTS` — 호출자 / 호출자 도메인 기준) 중 하나라도
  `ALIVE`인 모든 `name`에 대해 entry를 반환. 없는 row는 merge에 `{}`로
  기여. `DOMAIN` 스코프는 merge에 포함되지 않음. merge 규칙은 §5.
- WebUI는 문서별 `mergedConfig`로 UI 상태 초기화하고, raw view들도
  보유해 "설정 페이지"에서 사용자-변경 vs 유저-기본값을 대조.

### S3. 사용자가 본인 문서 저장

사용자가 자신의 `preferences` 문서를 replace — 예: 언어, 실험적 기능
토글, 테이블별 표시 컬럼. self-service `updateMyAppConfig`를 호출합니다
— scope / scopeId는 서버가 `USER` + `current_user.user_id`로 자동 주입
하므로 입력은 `name` + `config`만. payload로 재계산된 `MyAppConfig`
(merged view 포함)를 직접 받으므로 별도 `myAppConfigs` 재조회가 필요
없습니다.

```graphql
mutation SaveMyConfig($input: UpdateMyAppConfigInput!) {
  updateMyAppConfig(input: $input) {
    myAppConfig {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
      updatedAt
    }
  }
}
```

```json
{
  "input": {
    "name": "preferences",
    "config": {
      "language": "ko",
      "experimentalFeatures": { "multiNodeScheduler": true }
    }
  }
}
```

- 권한: 인증된 유저. 서버가 `scopeId = current_user.user_id`를 주입
  하므로 다른 사용자 row를 건드릴 수 없음 (admin이 타인 row를 고쳐야
  하면 `adminUpdateAppConfig` 경로).
- 입력 `config`는 USER row의 `userCustomizedConfig`를 통째로 replace.
  `MyAppConfig.mergedConfig`는 read-only computed이므로 직접 쓸 수 없음.
- **Replace** 의미: 유지하려는 값이 있다면 같은 payload에 모두 보내야 함
  — partial-merge나 per-key patch 없음.
- **첫 쓰기 vs 이후 쓰기**: `updateMyAppConfig`는 `ALIVE` USER row가
  없으면 에러. 처음 저장하거나 soft-delete 이후 복귀할 때는 같은
  `name` / `config`로 `createMyAppConfig` 호출 (soft-deleted 상태라면
  `restoreMyAppConfig` 후 `updateMyAppConfig`). 클라이언트는
  `myAppConfigs` 엔트리의 `userCustomizedConfig` 존재 여부로 분기
  가능.

### S4. Admin이 도메인 유저 기본값 문서 발행

도메인 admin이 해당 도메인의 모든 유저가 merge base로 물려받을
`theme` 문서를 새로 발행 — `theme`은 유저 스토리상 admin 전용이므로
도메인 테마가 유저에게 도달하는 유일한 경로가 이 발행. 첫 발행은
`adminCreateAppConfig`를 `key.scope = DOMAIN_USER_DEFAULTS`로 호출,
이후 같은 문서의 수정은 `adminUpdateAppConfig`. `DOMAIN` 스코프
발행(admin-enforced 정책, 예: 도메인 전용 내부 설정 문서)도 같은
mutation을 `key.scope = DOMAIN`으로 호출 — 단 DOMAIN 값은
`myAppConfigs` merge에 포함되지 않으므로 유저가 값을 읽어야 하는
문서라면 `DOMAIN_USER_DEFAULTS`로 발행해야 함.

```graphql
mutation AdminCreateAppConfig($input: AdminCreateAppConfigInput!) {
  adminCreateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config updatedAt }
  }
}
```

```json
{
  "input": {
    "key": {
      "scope": "DOMAIN_USER_DEFAULTS",
      "scopeId": "default",
      "name": "theme"
    },
    "config": {
      "mode": "dark",
      "accent": "#6f5ae8"
    }
  }
}
```

- 권한: admin 필요 — service가 비-admin의 admin 경로 호출을 거부.
- 내부적으로 service가 §2의 해당 repository로 라우팅해 새 `ALIVE`
  row를 엄격 insert. 같은 key에 row가 있으면(ALIVE/DELETED 무관) 에러
  — admin은 `adminUpdateAppConfig` (ALIVE인 경우) 또는
  `adminRestoreAppConfig` (DELETED인 경우)를 대신 사용.
- 효과: 같은 도메인 사용자가 다음 `myAppConfigs` 호출 시 갱신된
  defaults가 merge되어 반환 (규칙은 §5).

### S5. Admin이 특정 사용자 문서를 대신 seed

운영 문의 대응 등으로 Admin이 사용자 A의 `preferences`
`userCustomizedConfig`를 처음으로 채워줌 — 타인 row를 건드리는
상황이므로 self-service `createMyAppConfig`가 아닌 admin 경로
`adminCreateAppConfig`를 `key.scope = USER` + `key.scopeId = 사용자
A의 user_id`로 호출. `create`는 사용자 A에게 이미 `preferences` row가
있으면(ALIVE/DELETED 무관) 에러이므로, ALIVE인 경우 admin은 같은 입력
형태로 `adminUpdateAppConfig`, DELETED인 경우 `adminRestoreAppConfig`
로 폴백. merged `config`(`MyAppConfig.mergedConfig`)는 항상 read-only
이며 직접 쓸 수 없음.

```graphql
mutation AdminCreateAppConfigForUser($input: AdminCreateAppConfigInput!) {
  adminCreateAppConfig(input: $input) {
    appConfig { id scope scopeId name status config updatedAt }
  }
}
```

```json
{
  "input": {
    "key": {
      "scope": "USER",
      "scopeId": "00000000-0000-0000-0000-000000000123",
      "name": "preferences"
    },
    "config": { "experimentalFeatures": { "multiNodeScheduler": true } }
  }
}
```

- `USER` 스코프에서 `config` 입력은 대상 사용자의
  `userCustomizedConfig`로 저장.
- `adminCreateAppConfig`는 `DELETED` row를 revive하지 *않음* — 그
  역할은 `adminRestoreAppConfig`. `create`는 기존 row가 있으면 status
  무관하게 에러.
- 응답은 raw `AppConfig` — 대상 사용자의 merged view는 해당 유저
  세션이 다음 `myAppConfigs` 호출 시 새 `userCustomizedConfig` +
  같은 `name`의 도메인 defaults merge 결과로 반영.

### S6. Admin이 전체 AppConfig 감사 (cross-scope 검색)

"최근 1주일 내 `theme`을 건드린 모든 도메인" 또는 "`menu` 문서를
customize한 모든 도메인" 같은 케이스:

```graphql
query AuditConfigs(
  $filter: AppConfigFilterGQL!
  $orderBy: [AppConfigOrderByGQL!]
  $first: Int
  $after: String
) {
  adminAppConfigs(filter: $filter, orderBy: $orderBy, first: $first, after: $after) {
    edges {
      cursor
      node { id scope scopeId name status config updatedAt }
    }
    pageInfo { hasNextPage endCursor }
    count
  }
}
```

```json
{
  "filter": {
    "scope": { "in": ["DOMAIN", "DOMAIN_USER_DEFAULTS"] },
    "name": { "equals": "theme" },
    "updatedAt": { "gte": "2026-04-14T00:00:00Z" }
  },
  "orderBy": [{ "field": "UPDATED_AT", "direction": "DESC" }],
  "first": 50
}
```

- 서버: `check_admin_only()` → Connection 검색. cursor 모드라 정렬은
  cursor key로 고정. 기본적으로 `ALIVE` row만 반환.

### S7. 운영자가 문서 전체 제거 (soft-delete)

오래된 / 폐지된 문서 제거 — 예: 도메인의 구식 `legacy_menu` 문서 폐기:

```graphql
mutation RemoveDomainLegacyMenu($input: AdminDeleteAppConfigInput!) {
  adminDeleteAppConfig(input: $input) {
    appConfig { id scope scopeId name status updatedAt }
  }
}
```

```json
{
  "input": {
    "key": { "scope": "DOMAIN", "scopeId": "default", "name": "legacy_menu" }
  }
}
```

- 권한: admin 필요 (`admin*AppConfig`는 전부 admin 전용).
- service가 매칭 row의 `status`를 `DELETED`로 설정. 이후
  조회(`Domain.appConfigs`, `UserNode.appConfigs`, `adminAppConfigs`
  등)는 해당 문서를 숨김.
- **Idempotent**: row가 없거나 이미 `DELETED`이면 no-op.
- **복구 가능**: 같은 `key`로 `adminRestoreAppConfig`를 호출하면 row
  가 `ALIVE`로 복귀하며 저장값은 그대로 유지. 복구 후 값을 바꾸려면
  `adminUpdateAppConfig`를 이어서 호출. `adminCreateAppConfig`는
  revive하지 않음 — 기존 row가 있으면 에러.

사용자가 본인 문서를 제거할 때는 self-service 경로 `deleteMyAppConfig`
를 사용 — `name`만 입력, 서버가 `scope=USER` + `scopeId =
current_user.user_id`를 주입. payload로 delete 이후 재계산된
`MyAppConfig`(남은 `DOMAIN_USER_DEFAULTS`만 반영) 또는 source가 전부
사라진 경우 `null`을 받음.

```graphql
mutation RemoveMyConfig($input: DeleteMyAppConfigInput!) {
  deleteMyAppConfig(input: $input) {
    myAppConfig {
      name
      userCustomizedConfig
      domainDefaultConfig
      mergedConfig
      updatedAt
    }
  }
}
```

```json
{ "input": { "name": "preferences" } }
```
