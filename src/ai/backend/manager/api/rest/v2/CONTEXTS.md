# REST v2 API 레이어 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`, 구현 패턴은 `/api-guide` 스킬.

## 핸들러 의존성 주입 예시

```python
class V2DomainHandler:
    _adapter: DomainAdapter

    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    async def admin_search(self, body: BodyParam[T]) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
```

## scoped search URL 예시 (현재 패턴)

- `POST /v2/sessions/projects/{project_id}/search` — 프로젝트 내 세션
- `POST /v2/sessions/agents/{agent_id}/search` — 에이전트 위 세션
- `POST /v2/users/domains/{domain_name}/search` — 도메인 내 사용자
- `POST /v2/users/projects/{project_id}/search` — 프로젝트 내 사용자
- `POST /v2/users/roles/{role_id}/search` — 특정 role 사용자

## 페이지네이션 모드 동작

search 엔드포인트는 커서·오프셋 페이지네이션 인자를 모두 받는다.

- **기본(인자 없음):** 오프셋(`limit=10, offset=0`)으로 폴백.
- **오프셋(`limit`/`offset`):** 사용자 지정 `order` 적용, 없으면 엔티티 기본 정렬. 커스텀 정렬이 필요할 때.
- **커서(`first`/`after` 또는 `last`/`before`):** 정렬은 엔티티 커서 키(보통 `created_at` 또는 PK)로 고정.
  사용자 지정 `order`는 무시한다 — 커서 일관성을 위해 고정 정렬이 필요. 무한 스크롤/"더 보기" UX에 적합.
- 한 요청에 한 모드만. `first`+`limit` 혼용은 에러.
