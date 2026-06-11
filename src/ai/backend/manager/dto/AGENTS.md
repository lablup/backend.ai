# Manager DTO — 가드레일

> 이 DTO들을 쓰는 API 통합 패턴은 `/api-guide` 스킬 참고.

## 새 DTO를 어디에 둘까

| 사용 주체 | 위치 |
|-----------|------|
| Manager API 핸들러만 | `manager/dto/` |
| 여러 컴포넌트(agent, storage, client SDK) | `common/dto/manager/{domain}/` |

애매하면: `manager/` 밖에서 import하면 `common/dto/`에 둔다.

## DTO 규칙

- 모든 DTO는 `BaseRequestModel`(Pydantic v2)을 상속해야 한다.
- DTO는 직렬화·검증만 — 비즈니스 로직 메서드 금지.
- DTO 안에서 `manager/models/`의 ORM `Row` 타입을 import하지 않는다.
- 외부 호출자가 쓰는 DTO에 `data/` 도메인 타입을 import하지 않는다(의존 방향 유지: dto → common 타입만).

## 네이밍 규약

- 요청: `{Operation}{Entity}Req` — 예) `CreateUserReq`, `SearchSessionsReq`.
- 응답: `{Operation}{Entity}Response` — 예) `CreateUserResponse`.
- 경로 파라미터: `{Entity}PathParam` — 예) `ArtifactPathParam`.
