# REST v2 API 계층: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있고, 구현 패턴은 `/api-guide` 스킬에 있다.

## adapter 의존과 동작 surface

handler 는 동작을 갖지 않는다. 모든 handler 가 엔티티별 공유 adapter(`api/adapters/`)를 호출한다. 등록은 gate 를 그대로 따른다. `admin_*` handler 는 `superadmin_required` 로 등록하고, bare global 읽기는 `auth_required` 만으로 등록하며(public 읽기), scoped search 는 요청 body 에서 scope 를 받는다.

## handler 의존성 주입 예

```python
class V2DomainHandler:
    _adapter: DomainAdapter

    def __init__(self, *, adapter: DomainAdapter) -> None:
        self._adapter = adapter

    async def admin_search(self, body: BodyParam[T]) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
```

## scoped search URL

- 엔티티마다 `scoped/search` endpoint 하나를 두고, 호출자가 전달한 scope 를 body 에서 받는다(예: `scheduling_history/` 아래 `POST .../kernels/scoped/search`, `POST .../replica-groups/scoped/search`).
- legacy 패턴: 부모가 고정된 경로(`POST /v2/sessions/projects/{project_id}/search`, `POST /v2/users/domains/{domain_name}/search` 등). 새로 추가하지 않는다. scope 는 URL segment 가 아니라 요청 데이터다.

## pagination 모드 동작

search endpoint 는 cursor 와 offset pagination 인자를 모두 받는다.

- **기본(인자 없음):** offset 으로 대체한다(`limit=10, offset=0`).
- **offset(`limit`/`offset`):** 사용자가 지정한 `order` 를 적용하고 없으면 엔티티의 기본 정렬을 적용한다. custom 정렬이 필요할 때 사용한다.
- **cursor(`first`/`after` 또는 `last`/`before`):** 정렬을 엔티티의 cursor key(보통 `created_at` 이나 primary key)로 고정한다. 사용자가 지정한 `order` 는 무시한다. cursor 일관성에는 고정 정렬이 필요하다. infinite scroll 이나 "load more" 사용자 경험 에 적합하다.
- 요청마다 모드 하나만 사용한다. `first` 와 `limit` 을 섞으면 에러다.
