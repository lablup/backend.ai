# Manager GraphQL 레이어 — 가드레일

> 배경(federation 충돌·페이지네이션 동작)은 같은 디렉터리 `CONTEXTS.md`, 구현 패턴은 `/api-guide` 스킬(GraphQL Patterns).

## 타입 네이밍

- 모든 Strawberry 타입은 **Python 클래스 이름**에 `GQL` 접미를 붙인다: `DomainGQL`, `DomainFilterGQL`, `DomainScopeGQL`.
- 출력/입력/connection 타입 모두 적용.
- **스키마 노출 이름**에는 `GQL`이 없어야 한다. 데코레이터에 `name=`(클래스명에서 `GQL` 제거)을 항상 넘긴다
  (예: `CreateDomainInputGQL` → `name="CreateDomainInput"`). `name=` 누락 시 SDL에 `GQL`이 샌다.
- v1 Graphene 타입과 이름이 충돌하면 `V2` 접미 스키마명을 쓴다(`name="KeyPairV2"`). 배경은 `CONTEXTS.md`.

## 데코레이터

- `@strawberry.type/input/field/enum/mutation`, `@strawberry.experimental.pydantic.*`를 직접 쓰지 않는다.
- `decorators.py`의 커스텀 데코레이터만 쓴다:
  - `@gql_node_type` — Relay Node 타입(`PydanticNodeMixin[DTO]` 상속)
  - `@gql_pydantic_type(model=DTO)` — v2 Pydantic DTO 기반 출력 타입·payload
  - `@gql_pydantic_input` — 입력 타입(`PydanticInputMixin[DTO]` 상속)
  - `@gql_pydantic_interface(model=DTO)` — DTO 기반 interface
  - `@gql_connection_type` — `Connection[T]`/`Edge[T]` 서브클래스
  - `gql_field` / `gql_added_field` — 부모 타입과 함께 도입한 필드 / 이후 추가 필드(자체 버전)
  - `@gql_root_field` — Query 타입의 루트 쿼리 필드(항상 버전 표기)
  - `gql_enum` / `@gql_enum`, `@gql_mutation`, `@gql_subscription`, `@gql_federation_type`
- Pydantic DTO 요구를 우회하려 새 데코레이터를 추가하지 않는다.

## 버전 메타데이터

- 새 타입·필드·enum·mutation 추가 시 `added_version`에 `NEXT_RELEASE_VERSION` 상수를 쓴다 — 버전 문자열을
  하드코딩하지 않는다(릴리스 시 `scripts/release.sh`가 동결). 이미 릴리스된 리터럴 버전은 바꾸지 않는다.
  ```python
  from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
  @gql_root_field(BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="..."))
  async def my_foo(...): ...
  ```

## import

- Strawberry 타입을 `TYPE_CHECKING` 블록 안에서 import하지 않는다 — Strawberry는 런타임에 타입을 평가하므로
  조용히 실패하거나 에러난다. 항상 모듈 레벨에서 import한다.

## 교차 엔티티 참조

- 순환 import를 피하려 교차 엔티티 node 참조에는 `strawberry.lazy()`를 쓴다
  (`Annotated[T, lazy(...)] | None` 문법은 `/api-guide`).

## N+1 방지

- resolver 안에서 관련 엔티티를 개별 fetch 함수로 가져오지 않는다.
- 교차 엔티티 로딩은 항상 `info.context.data_loaders.*`를 쓴다.

## Service 호출

- resolver는 Adapter(`info.context.adapters.*`)를 통해서만 service를 호출한다 — Processor/Service 직접 호출 금지.
- Adapter는 Pydantic DTO(`common/dto/manager/v2/`)를 받고 반환한다.

## Pydantic DTO 통합

GQL 타입은 v2 DTO(`common/dto/manager/v2/`)의 얇은 래퍼다.

- Node: `PydanticNodeMixin[DTO]` 상속 + `@gql_node_type`. `FooGQL.from_pydantic(dto)`로 변환.
- 중첩 출력/payload: `@gql_pydantic_type(model=DTO)`. `from_pydantic()` 자동 생성.
- 입력: `PydanticInputMixin[DTO]` 상속 + `@gql_pydantic_input`. `input_gql.to_pydantic()`로 변환.
- GQL enum 값은 DTO enum 값과 정확히 일치해야 한다(`.value`로 변환). GQL 필드명은 DTO 필드명과 일치.
- GQL의 `strawberry.UNSET`은 `to_pydantic()`에서 DTO의 `SENTINEL` 기본값으로 자동 매핑.

## 에러 처리 & nullable 스키마

- 객체를 못 찾을 수 있는 쿼리/resolver는 반환 타입을 **nullable**(`T | None`)로 선언한다.
- `None`을 반환하려고 fetcher에서 도메인 예외(`NotFound` 등)를 잡지 않는다 — 예외를 전파한다.
  Relay 스펙상 `resolve_nodes`만 `Iterable[Self | None]`을 반환할 수 있다.

## 쿼리 페이지네이션 인자

모든 search/list 쿼리는 아래 인자 그룹을 **전부** 제공한다 — 하나도 빼지 않는다:
- `filter: XxxFilterGQL | None`
- `order_by: list[XxxOrderByGQL] | None`
- `before/after: str | None`, `first/last: int | None` (커서)
- `limit/offset: int | None` (오프셋)

클라이언트가 커서·오프셋을 자유롭게 선택할 수 있어야 한다. 모드별 동작은 `CONTEXTS.md`.

## Admin & 스코프

- superadmin 전용 resolver: 첫 줄에서 `check_admin_only(info)`를 호출한다.

**search — 세 변형:**
- `adminFoosV2`: superadmin 전용, 스코프 없음 — 전체 시스템.
- `scopedFoosV2`(예: `scopedSessionsV2`): non-admin, 스코프 필수 — 해당 스코프 내.
- `myFoosV2`: self-service, adapter가 현재 사용자를 스코프로 내부 resolve.
- non-admin에게 "스코프 없는 전체 조회"는 없다.

**scoped search 규약:**
- 쿼리명 `scopedFoosV2`(엔티티당 단일 루트 필드).
- scope는 엔티티별 입력(`FooScopeGQL`, `api/gql/{entity}/types/scope.py`)으로 받는 **필수 인자** — bare ID 금지.
  shape는 엔티티별(단일 ID / 엔티티 태그 ref 리스트 / 카테고리별 리스트).
- 비어있지 않음 검증은 DTO의 Pydantic `model_validator`에 둔다 — GQL/REST 경계에서 균일하게 거부.
- resolver는 scope를 search 입력 DTO와 함께 adapter에 넘긴다. 인가(RBAC)는 adapter/service 책임 — resolver가 아님.
- 레거시 `{scope}FoosV2`(예: `projectSessionsV2`)는 이 규약 이전 — 새로 만들지 않는다.

**`myFoosV2` resolver:**
- resolver는 `current_user()`를 호출하거나 스코프를 만들지 않는다 — search 입력 DTO만 adapter에 넘긴다.
- adapter가 내부에서 `current_user()`로 스코프를 구성한다.

**create / update / get / delete / purge — `admin_` 분리 기준:**
- admin 전용 엔티티: 단일 `admin_` mutation/query.
- admin·사용자 둘 다이고 동작 다름: `admin_`·non-admin 분리(서로 다른 입력 타입).
- 권한 검사만 다름: 단일 — admin은 이미 접근 권한 있음.

## 레거시

- `gql_legacy/`(Graphene) 패턴을 복사하지 않는다 — Strawberry로 이행 중.
