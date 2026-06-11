# Manager Repositories 레이어 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`.

## ops provider로의 점진 이행

`ops/base/provider.py`의 `DBOpsProvider`가 표준 경로다. db_source는 ops로 점진 이행 중 —
신규/수정은 ops를 쓰고 기존은 건드릴 때까지 둔다. 엔진을 격리해 raw 세션이 호출자에게 새지 않게
하고, spec 타입만 받아 임의 SQL이 레이어를 넘지 못하게 한다.

## tx를 한 메서드에 모으는 이유

세션을 public 메서드에서 열고 닫아 tx 경계를 명확히 한다. 여러 동작을 한 service 호출로 묶으면
부분 커밋 없이 원자성을 보장할 수 있다. 메서드를 잘게 쪼개면 호출자가 여러 tx에 걸쳐 일관성을 잃는다.

## spec이 테이블 하나만 소유하는 이유

다중 테이블 쓰기를 spec에 숨기면 순서·의존성이 가려진다. repository가 부모→자식 순서를 절차적으로
드러내고 `DependentCreatorSpec`로 의존을 명시한다.

## 스코프 필터 기본값

`batch_query_with_scopes`가 기본인 건 RBAC 스코프를 강제하기 위해서다. `batch_query_in_global`은
필터를 우회하므로 superadmin/내부 경로로 제한하고, 빈 스코프는 `EmptySearchScopeError`로 막는다.
