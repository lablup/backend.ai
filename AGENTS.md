# AI 코딩 에이전트 가이드라인

이 파일은 AI 코딩 에이전트의 핵심 규칙을 담는다. 상세 패턴·워크플로는 아래 스킬과 문서를 쓴다.

## 문서 구조 (AGENTS.md / CONTEXTS.md)

- **`AGENTS.md`**: 가드레일(규칙)만. 단정형으로 간결하게. 항상 자동 로드된다(`CLAUDE.md`는 이 파일로의 심링크).
- **`CONTEXTS.md`**: 개발을 위해 읽는 배경(가정·근거·caveat·예시·개발 맥락). 가정 등이 바뀌면 비교적 자주
  갱신된다. 온디맨드로 읽으며, 해당 `AGENTS.md` 상단에 포인터를 둔다.
- **`README.md`**: 사람이 컴포넌트 구성을 이해하기 위한 문서. 자주 바뀌지 않아야 한다. AGENTS/CONTEXTS와 중복하지 않는다.
- 규칙은 적용 범위의 **가장 상위에 한 번만** 둔다 — 전역은 이 root, 컴포넌트 전역은 컴포넌트 최상위.
  하위에서 상위 규칙을 중복하지 않는다.

## 문서 인덱스

**핵심 문서 (직접 읽기):**
- `tests/AGENTS.md` — 테스트 가이드라인·전략
- `BUILDING.md` — 빌드 시스템, 품질 강제, BUILD 정책
- `src/ai/backend/manager/models/alembic/README.md` — Alembic 마이그레이션 백포트 전략
- `README.md` — 프로젝트 개요·아키텍처
- `proposals/README.md` — BEP (Backend.AI Enhancement Proposals)

**스킬 (`/skill-name`으로 호출):**

언제 쓰나:
- 기능 설계 → `/bep-guide`
- repo/service/API 레이어 구현 → `/repository-guide`, `/service-guide`, `/api-guide`
- SDK/CLI 코드 구현 → `/cli-sdk-guide`
- 테스트 작성 → `/tdd-guide`
- 코드 변경 후 서비스 재시작 → `/local-dev`
- **`./bai` 명령 실행 → `/bai-cli` (실행 전 반드시 로드)**
- 개발 중 로그/메트릭/트레이스 확인 → `/observability` (Grafana MCP)
- Docker/halfstack 문제 → `/halfstack`
- DB 마이그레이션 확인/적용 → `/db-status`, `/db-migrate`
- 컴포넌트 서버 직접 실행 → `/cli-executor`
- PR 제출 → `/submit`
- 릴리스 준비 → `/release`

스킬 소스: `.claude/skills/{name}/SKILL.md`

## 절대 규칙 (전역)

**품질 강제를 우회하지 않는다:**
- 린터 경고를 `# noqa`로 억누르지 않는다.
- 타입 에러를 `# type: ignore`로 억누르지 않는다.
- 품질 문제는 내 변경과 무관해도 즉시 고친다.

**Python 핵심 규칙:**
- **Async-first**: 모든 I/O는 async/await를 쓴다.
- **예외**: 가능하면 모든 곳에서 `BackendAIError`를 상속한다 — 비즈니스 로직에서 빌트인 예외를 직접 raise하지 않는다.
- **import**: 부모 상대 import(`from ..module`)를 쓰지 않는다 — 절대 import를 쓴다.
- **re-export**: 가능하면 `__init__.py` re-export를 쓰지 않고 모듈을 직접 import한다.
- **클래스 필드**: 클래스가 쓰는 인스턴스 필드는 클래스 본문 최상위에 타입과 함께 선언한다(할당은 `__init__`에서).

**BUILD 파일:**
- ❌ `src/` 디렉터리에는 BUILD 파일을 추가하지 않는다.
- ✅ 새 테스트 디렉터리에는 BUILD 파일을 반드시 추가한다.
- 테스트 모듈은 `python_tests()`, 유틸리티는 `python_testutils()`.

## 커밋 전

커밋 전, 아래 명령을 실행하고 모든 에러를 고친다:

```bash
pants fmt --changed-since=HEAD~1
pants fix --changed-since=HEAD~1
pants lint --changed-since=HEAD~1
pants check --changed-since=HEAD~1
pants test --changed-since=HEAD~1
```

**lint·타입·테스트 에러는 모두 고친다 — 억누르거나 건너뛰지 않는다.**

**API/CLI 변경 후에는 `./bai` CLI로 라이브 서버에서 검증하고, Grafana MCP(`/observability`)로 런타임 로그/메트릭을 확인한다.**
**`./bai` 명령 실행 전 반드시 `/bai-cli` 스킬을 로드한다.** 이 스킬에 엔티티-명령 레퍼런스가 있어, 없으면 명령을 잘못 추측한다.
서비스 재시작은 `/local-dev`, docker 서비스 변경은 `/halfstack` 스킬 참고.

## Alembic 마이그레이션 백포트

릴리스 브랜치로 마이그레이션을 백포트할 때는 백포트와 main 브랜치 마이그레이션 모두 멱등이어야 한다.
전체 전략·예시는 `src/ai/backend/manager/models/alembic/README.md` 참고.

## 레이어 아키텍처

API Handler → Processor → Service → Repository → DB

- API 핸들러는 Processor를 호출한다 — Service를 직접 호출하지 않는다.
- Service는 Action(frozen dataclass)을 받아 ActionResult를 반환한다.
- Repository가 모든 DB 접근을 담당한다(트랜잭션·세션은 repository 소관).
- 하위 레이어에서 상위 레이어를 import하지 않는다.
- 상세 패턴은 스킬 참고: `/repository-guide`, `/service-guide`, `/api-guide`.

## API 개발 규칙

**모든 신규 기능은 풀스택에서 v2 패턴을 쓴다:**
- REST API: `api/rest/v2/{entity}/` (REST v1에 새 엔드포인트 추가 금지)
- DTO: `common/dto/manager/v2/{entity}/` (GQL·REST v2 공유)
- GraphQL: Strawberry 기반 `api/gql/{entity}/` (`gql_legacy/`에 추가 금지)
- Adapter: `api/adapters/{entity}.py` (GQL·REST v2 공유)
- Client SDK: `client/v2/domains_v2/{entity}.py` (타입드 Pydantic 요청/응답)
- CLI: `client/cli/v2/{entity}/` (SDK v2 호출)

**엔티티당 표준 6개 연산:** create, get, search, update, delete, purge
- 상세 API 패턴: `/api-guide`
- SDK/CLI 패턴: `/cli-sdk-guide`

**신규 API 엔드포인트 구현 후 라이브 서버로 검증한다** — admin·non-admin 모두 확인. 서버 재시작·`./bai`
테스트·로그 확인 절차는 `/local-dev`, `/bai-cli`, `/observability` 스킬 참고.

## 개발 가이드라인

**문서 우선:** 변경 전 해당 디렉터리의 `AGENTS.md`를 읽고, 더 많은 맥락이 필요하면 같은 디렉터리 `CONTEXTS.md`를 읽는다.

**BEP 우선:** 중요 기능은 `/bep-guide` 스킬을 쓴다. `proposals/README.md`에서 기존 BEP를 확인하거나 새로 만든다.

**TDD:** 테스트를 먼저 쓴다. 워크플로는 `/tdd-guide` 스킬, 전략은 `tests/AGENTS.md` 참고.

**구현 패턴:** 상세는 스킬을 쓴다:
- Repository 레이어 → `/repository-guide`
- Service 레이어 → `/service-guide`
- API/GraphQL → `/api-guide`
