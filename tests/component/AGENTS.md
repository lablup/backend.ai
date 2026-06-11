# 컴포넌트 테스트 — 가드레일

> 실제 aiohttp 서버 + 실제 DB로 HTTP API 레이어를 테스트한다.
> 비즈니스 로직은 `tests/unit/`에서 검증한다 — 여기서 중복하지 않는다.

## 여기서 테스트할 것

- HTTP 라우팅, auth 데코레이터, 요청/응답 직렬화.
- 역할별 동작 차이(superadmin vs 사용자 keypair).
- API 경계에서 잘못된 입력에 대한 에러 응답.

## 핵심 픽스처

`create_app_and_client`(`AppBuilder`) — 선택적 `cleanup_contexts`로 실제 aiohttp 서버를 띄운다.
`AppBuilder` 프로토콜로 `(app, client)`를 반환:
```python
async def test_something(create_app_and_client: AppBuilder) -> None:
    app, client = await create_app_and_client(...)
```

`get_headers(keypair, method, path, ...)` — 서명된 HMAC auth 헤더 생성.
- auth 헤더를 직접 만들지 않는다 — 항상 이 픽스처를 쓴다.

## BUILD 파일

- 새 하위 디렉터리마다 `python_tests()`를 담은 `BUILD` 파일이 필요하다.

## 여기 속하지 않는 것

- 비즈니스 로직 단언(service 동작) → `tests/unit/`.
- 전체 E2E 사용자 워크플로(create → list → delete) → `tests/integration/`.
- raw `aiohttp.ClientSession` 사용 — 항상 제공된 픽스처를 거친다.
