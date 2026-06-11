# Manager Repositories 레이어 — 가드레일

> 배경은 같은 디렉터리 `CONTEXTS.md`, 구현 패턴은 `/repository-guide` 스킬.

## 디렉터리 구조 (도메인별)

- `repository.py`(단일 엔티티 CRUD), `repositories.py`(다중 엔티티 컨테이너 / `RepositoryArgs`),
  `types.py`(SearchScope + SearchResult), `options.py`(QueryCondition/QueryOrder),
  `db_source/db_source.py`(쿼리). 선택: `creators.py` / `updaters.py` / `purgers.py` / `upserters.py`.
- db_source를 분리해 Repository가 어떤 source를 쓰는지 구분되게 한다.

## 메서드 네이밍

- getter는 `get_` 없이 엔티티 이름: `user(id)`, `session(id)`.
- 표준 6개: `create` / `{entity}` / `search` / `update` / `delete` / `purge`.

## 데이터 접근

- 일반 API 경로는 `DBOpsProvider`(`write_ops` / `read_ops`) 사용 권장. 내부 동작은 db를 직접 써도
  되지만, repository로 분리하는 것을 기본으로 한다.
- ops는 기본 provider를 쓰고, sokovan 등 특정 상황의 공통 동작용 provider만 따로 둔다.
- ops 메서드는 spec 타입(Querier/Creator/Updater/Upserter/Purger, `DependentCreatorSpec`)만 받는다.
  spec 하나는 테이블 하나만 소유한다.
- 다중 테이블 쓰기는 spec 안에서 하지 않는다. repository가 부모를 먼저 생성하고, 그 결과로 의존 값을
  구성해 `create_dependent` / `bulk_create_dependent`에 `DependentCreatorSpec`로 넘긴다.
- 읽기 기본은 `batch_query_with_scopes`. `batch_query_in_global`은 superadmin/내부 경로 전용.

## 트랜잭션

- 격리 수준은 항상 READ COMMITTED.
- ops를 받은 한 메서드 안에서 작업을 끝내 tx를 보장한다.
- db 직접 사용 시 service/동작 단위로 repository 메서드를 한 번에 처리한다. 분리는 명확한 레이어
  경계가 있을 때만 두고, service 동작에 repository 메서드를 맞춰 쓴다.
- db session은 public 메서드에서만 생성하고, private 메서드에서만 재활용한다.

## SearchScope

- `@dataclass(frozen=True)`, `to_condition() -> QueryCondition`(`types.py`) 구현.

## 여기 속하지 않는 것

- 비즈니스 로직 / 도메인 검증 (services/ 소관).
- `Row` 직접 노출 — 반환 전 `data/` 타입으로 변환.
