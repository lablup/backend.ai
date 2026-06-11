# 테스트 가이드라인 — 가드레일

> 배경·근거는 같은 디렉터리 `CONTEXTS.md`. TDD 워크플로·패턴·코드 예시는 `/tdd-guide` 스킬, BUILD 정책은 `BUILDING.md`.

## 어느 디렉터리에 둘까

| 테스트 대상 | 디렉터리 |
|-------------|----------|
| Service / handler 로직(모킹) | `tests/unit/{component}/` |
| Repository / Model(실 DB, `with_tables`) | `tests/unit/{component}/repositories/` |
| HTTP API 레이어(실 aiohttp 서버 + DB) | `tests/component/{component}/` |
| E2E 사용자 시나리오(Client SDK v2) | `tests/integration/` |

각 디렉터리는 자체 `AGENTS.md`에 셋업 패턴을 둔다.

## 테스트 전략

- **Repository / Model**: 실제 DB(`ai.backend.testutils.db.with_tables`)·실제 Redis로 실제 상호작용(쿼리·
  트랜잭션·제약)을 검증한다. DB 호출을 모킹하지 않는다.
- **Service / Handler / Controller**: 모킹 유닛 테스트. repository 호출·외부 의존성을
  `unittest.mock.AsyncMock`으로 모킹하고 비즈니스 로직을 검증한다.
- 구분 근거는 `CONTEXTS.md`.

## 무엇을 테스트하나 (구현이 아니라 동작)

관찰 가능한 계약을 테스트한다 — 동작이 같은 리팩터에도 살아남는 테스트가 좋은 테스트다.

- **테스트할 것**: 코드가 강제하는 제약/전제(예: 빈 스코프 → `EmptySearchScopeError`), 메서드가 호출자에게
  한 약속(추상화 보장), 실제 결과(`with_tables`로 create→read-back, update 반영, purge 제거, scoped 필터링).
- **테스트하지 말 것**: 구현 디테일·내부 호출 배선 스파이, 하위 레이어가 이미 검증한 위임 로직. (예시는 `CONTEXTS.md`)

## 테스트 구조

- 대상 단위(클래스/모듈/함수)별로 테스트 클래스로 묶는다.
- 테스트 조건은 인라인 셋업이 아니라 fixture로 표현한다.
- 함수는 간결하게: Arrange(fixture) → Act → Assert.
- 다른 테스트 파일에서 import하지 않는다 — 공용 유틸은 `conftest.py`나 `ai.backend.testutils`.
- 패턴·예시는 `/tdd-guide` 스킬.

## `with_tables` 핵심 규칙

- 모든 `Row` 의존성을 포함한다(SQLAlchemy 문자열 관계 — `RowA`가 `RowB`와 관계면 둘 다 넣는다).
- FK 순서대로(부모 먼저). 각 Row의 `relationship()`을 따라 체인을 추적한다.
- 관련 Row를 `# noqa: F401` 없이 모두 import해 `with_tables`에 넣는다.

## 테스트 타입 힌트

- 모든 테스트 코드는 완전한 타입 어노테이션을 가진다: fixture 참조·함수 반환·테스트 함수(`-> None`).
  mock은 필요 시 `typing.Protocol`/`TypedDict`.

## BUILD 파일

- 새 테스트 디렉터리마다 `BUILD`를 추가한다: 테스트 모듈 `python_tests()`, 공용 유틸 `python_testutils()`.
- 의존성을 명시하지 않는다 — Pants가 import에서 추론한다. 상세는 `BUILDING.md`.
