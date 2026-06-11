# 유닛 테스트 — 가드레일

> TDD 워크플로는 `/tdd-guide` 스킬, `with_tables` 패턴은 `tests/AGENTS.md` 참고.

## 디렉터리 레이아웃

`src/ai/backend/{component}/`를 그대로 미러링: `tests/unit/{component}/services/`,
`tests/unit/{component}/repositories/` 등.

## Service / Handler 테스트 (모킹)

- repository 호출은 `unittest.mock.AsyncMock`으로 모두 모킹한다.
- 실제 DB나 실제 aiohttp 서버를 띄우지 않는다 — `tests/component/` 소관.
- 대상 클래스당 테스트 클래스 하나, 의미 있는 동작당 테스트 함수 하나.

## Repository / Model 테스트 (실제 DB)

- `tests/unit/{component}/repositories/` 아래 둔다.
- `ai.backend.testutils.db`의 `with_tables`를 실제 `database_engine` 픽스처와 함께 쓴다.
- 모든 `Row` 의존성을 FK 순서(부모 먼저)로 나열한다.
- DB 호출을 모킹하지 않는다 — 실제 쿼리·제약을 검증하는 것이 목적.

## BUILD 파일

- 새 테스트 디렉터리마다 `python_tests()`를 담은 `BUILD` 파일이 필요하다.
- 공용 픽스처는 `conftest.py`에 둔다 — 형제 테스트 파일에서 import 금지.

## 여기 속하지 않는 것

- 실제 aiohttp 서버 셋업(`create_app_and_client`) → `tests/component/`.
- `BackendAIClientRegistry`를 쓰는 E2E 시나리오 → `tests/integration/`.
