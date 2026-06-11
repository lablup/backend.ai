# Client SDK v2 — 가드레일

## 아키텍처

```
CLI v2 → SDK v2 (domains_v2/) → REST v2 API (/v2/...)
```

SDK v2 도메인 클라이언트는 `client/v2/domains_v2/{entity}.py`에 둔다.
각 클라이언트 클래스는 `BaseDomainClient`를 상속하고 `self._client.typed_request()`를 쓴다.

## 네이밍 규약

- admin 메서드: `admin_search()`, `admin_create()`, `admin_update()`, `admin_delete()`, `admin_purge()`
- scoped search 메서드: 현재는 `{scope}_search()` — 예) `project_search(project_id, request)`, `domain_search(domain_name, request)`.
  **향후 방향(검토 중):** 서버 `scopedFoosV2` 규약에 맞춰 `scoped_search(request)`로 통일하고 scope는
  request DTO의 필드로 받는다. (URL 패턴·CLI 표면도 함께 정해야 함)
- self-service 메서드: `my_search()`, `my_issue()` — `/v2/{entity}/my/{operation}`에 매핑
- 사용자 대면 메서드: `get()`, `enqueue()`

**scoped search URL 패턴:**
- SDK 메서드는 `POST /v2/{entity}/{scope_type}/{scope_id}/search`를 호출한다.
- 예) `f"{_PATH}/projects/{project_id}/search"` (`f"{_PATH}/search-by-project/{id}"` 아님)
- `search-by-{scope}` URL 패턴을 쓰지 않는다.

## typed_request 패턴

```python
async def admin_create(self, request: CreateFooInput) -> FooPayload:
    return await self._client.typed_request(
        "POST", _PATH, request=request, response_model=FooPayload,
    )
```

- 요청/응답 모델은 `common/dto/manager/v2/{entity}/`에서.
- HTTP 메서드: POST(create/search/delete/purge), GET(get), PATCH(update).

## 새 엔티티 추가

1. 도메인 클라이언트 클래스를 담은 `domains_v2/{entity}.py` 생성
2. `v2_registry.py`에 `@cached_property`로 등록
