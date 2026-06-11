# REST v2 API 레이어 — 가드레일

> 배경(페이지네이션 동작·DI 예시·scoped URL 예시)은 같은 디렉터리 `CONTEXTS.md`, 구현 패턴은 `/api-guide` 스킬.
> REST v2는 `common/dto/manager/v2/`의 Pydantic DTO를 쓴다 — GQL 스키마와 같은 DTO(단일 원천).

## 아키텍처

```
REST v2 Handler → Adapter (api/adapters/) → Processor → Service → Repository
```

## 핸들러 스타일

- 모든 핸들러는 `APIHandler` 클래스의 메서드여야 한다.
- 요청은 `BodyParam[T]`로 파싱한다 — `T`는 `common/dto/manager/v2/`의 DTO.
- `APIResponse.build(status_code=..., response_model=payload)`로 반환 — `payload`도 v2 DTO.

## 핸들러 의존성 주입

- 각 핸들러는 **개별 adapter**를 주입받는다(Adapters 레지스트리가 아님): `self._adapter.method()` 호출 —
  `self._adapters.domain.method()` 금지.
- Adapter는 GQL 레이어와 공유한다 — REST 전용 adapter를 만들지 않는다.
- `admin_` 접두 adapter 메서드 → `superadmin_required` 미들웨어, non-admin → `auth_required`.

## DTO

- `common/dto/manager/v2/`의 DTO만 쓴다.
- `common/dto/manager/`(v1, 레거시 REST용)에서 import 금지.
- REST 전용 요청/응답 모델을 정의하지 않는다 — 공유 v2 DTO를 쓴다.

## 네이밍 & 스코프

- superadmin 전용: `admin_` 접두 + `superadmin_required` 미들웨어.
- scoped: 현재는 `{scope}_` 접두. **향후 방향(검토 중):** `scoped_`로 통일하고 scope를 요청 필드로 받는다(아래 참고).
- self-service: `/v2/{entity}/my/` — 엔티티 앞, `my`는 스코프 한정자.

**search — 항상 두 변형:**
- `POST /v2/{entity}/search`: superadmin 전용, 스코프 없음 — 전체 시스템 조회.
- scoped search(non-admin): 스코프 필수 — 해당 스코프 내 조회.
- non-admin에게 "스코프 없는 전체 조회"는 없다.

**scoped search URL** (검토 중):
- 현재: `POST /v2/{entity}/{scope_type}/{scope_id}/search` — 스코프를 중첩 리소스 경로로(`search-by-{scope}` 아님).
  예: `/v2/sessions/projects/{project_id}/search`. (예시 더 보기: `CONTEXTS.md`)
- **향후 방향:** `/v2/{entity}/scoped/search` 고정 path + scope를 요청 body 필드로(path param 아님).
  SDK `scoped_search`·GQL `scopedFoosV2`와 일관.
- 모든 scoped search 라우트는 `auth_required` 미들웨어.

**self-service(`my`):**
- `POST /v2/{entity}/my/{operation}` (예: `/v2/keypairs/my/search`). adapter가 `current_user()`로
  사용자를 resolve. `auth_required` 미들웨어.

**create / update / get / delete / purge — `admin_` 분리 기준:**
- admin 전용 엔티티: 단일 `admin_`.
- admin·사용자 둘 다이고 동작 다름: `admin_`·non-admin 분리(서로 다른 DTO).
- 권한 검사만 다름: 단일 — admin은 이미 접근 권한 있음.

## 페이지네이션

- 커서·오프셋 인자를 모두 받는다. 한 요청에 한 모드만 — `first`와 `limit` 혼용은 에러.
- 모드별 동작·기본값은 `CONTEXTS.md` 참고.

## 라우팅

- 라우트 등록은 `RouteRegistry`(REST v1과 동일 프레임워크)로, 도메인별 전용 registrar 함수에서.

## 여기 속하는 것 / 속하지 않는 것

- 속함: HTTP 요청/응답 변환, auth 미들웨어(`superadmin_required`, `auth_required`).
- 속하지 않음: 비즈니스 로직·도메인 규칙, 직접 DB 접근·ORM import, Repository/Service/Processor import,
  도메인 Data ↔ DTO 변환(Adapter 소관).
