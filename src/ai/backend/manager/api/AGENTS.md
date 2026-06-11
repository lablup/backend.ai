# Manager API 레이어 — 가드레일

> 배경·검증 절차는 같은 디렉터리 `CONTEXTS.md`, 구현 패턴은 `/api-guide` 스킬.

## 핸들러 스타일

- 모든 핸들러는 `APIHandler` 클래스의 메서드여야 한다 — 모듈 레벨 async 함수 금지.
- 요청은 `BodyParam[T]`, `PathParam[T]`로 파싱한다 — 핸들러 안에서 `request.json()`이나
  `request.rel_url.query`를 직접 읽지 않는다.
- `APIResponse.build(status_code=..., response_model=...)`로 반환한다 — `web.json_response()` 금지.

## Service 호출

- **신규(v2):** 핸들러는 Adapter(`self._adapters.{domain}.method(dto_input)`)를 호출한다 —
  Processor/Service 직접 호출 금지. Adapter는 GQL 레이어와 공유한다.
- **레거시 REST(v1):** 핸들러가 Processor를 직접 호출한다(`await self._foo.wait_for_complete(FooAction(...))`).
- 신규 API 엔드포인트는 모두 v2 패턴을 따른다.

## 네이밍 & 스코프

- superadmin 전용: `admin_` 접두 + 첫 줄에서 `_check_superadmin(request)` 호출.
- scoped: 현재는 `{scope}_` 접두 (예: `domain_search_users`). **향후 방향(검토 중):** `scoped_`로 통일하고
  scope를 요청 필드로 받는다(아래 scoped search REST URL 참고).
- self-service: `my_` 접두 (예: `my_keypairs`). Adapter가 사용자를 내부에서 resolve.
  - REST URL: `/v2/{entity}/my/{operation}` — 엔티티가 앞, `my`는 스코프 한정자.

**search — 항상 두 변형:**
- `admin_search_*`: superadmin 전용, 스코프 없음 — 전체 시스템 조회.
- scoped search: non-admin, 스코프 인자 필수 — 해당 스코프 내 조회.
- non-admin에게 "스코프 없는 전체 조회"는 없다.

**scoped search REST URL** (검토 중):
- 현재: `/v2/{entity}/{scope_type}/{scope_id}/search` — 스코프를 중첩 리소스 경로로 표현(`search-by-{scope}` 아님).
  예: `/v2/sessions/projects/{project_id}/search`.
- **향후 방향:** `/v2/{entity}/scoped/search` 형태의 고정 path를 쓰고 scope는 요청 body 필드로 받는다
  (path param이 아님). SDK `scoped_search`·GQL `scopedFoosV2`와 일관.

**create / update / get / delete / purge — `admin_` 분리 기준:**
- admin 전용 엔티티(Domain, ContainerRegistry 등): 단일 `admin_` 엔드포인트.
- admin·사용자 둘 다이고 동작이 다름(예: admin이 더 많은 필드 설정): `admin_`과 non-admin을 서로 다른 DTO로 분리.
- admin·사용자 둘 다이고 권한 검사만 다름: 단일 엔드포인트 — admin은 이미 엔티티 접근 권한이 있어 별도 `admin_` 불필요.

## 라우팅

- 라우트 등록은 `create_app()`에서만 한다.
- `app["prefix"]`를 이 sub-app의 URL 세그먼트로 설정한다.

## V2 DTO — 단일 진실 원천

v2 DTO(`common/dto/manager/v2/`)는 REST v2 핸들러, GQL 타입, Client SDK, CLI가 공유하는 스키마다.
**DTO 변경은 이 네 레이어 모두에 영향을 준다** — DTO → Adapter → REST 핸들러 → GQL 타입 → SDK → CLI 순으로 조율한다.

## 여기 속하는 것 / 속하지 않는 것

- 속함: HTTP 요청/응답 변환, auth 데코레이터(`@auth_required_for_method`).
- 속하지 않음: 비즈니스 로직·도메인 규칙, 직접 DB 접근이나 `manager/models/` ORM import,
  Repository/Service 클래스 import.
