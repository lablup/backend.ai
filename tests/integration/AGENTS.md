# 통합 테스트 — 가드레일

> Client SDK v2를 쓰는 풀스택 E2E 테스트. 사용자 대면 워크플로를 끝에서 끝까지 검증한다.

## 여기서 테스트할 것

- 완전한 사용자 관점 시나리오: create → read → update → delete 흐름.
- 역할 간 권한 경계(superadmin vs 일반 사용자).
- 여러 API 호출이나 컴포넌트에 걸친 동작.

## `@pytest.mark.integration` 마커

**클래스 레벨**에 붙인다 — 여기의 모든 테스트 클래스에 필수:
```python
@pytest.mark.integration
class TestUserLifecycle:
    async def test_full_user_lifecycle(self, admin_registry, ...) -> None:
```

## 핵심 픽스처

`admin_registry` — superadmin keypair를 가진 `BackendAIClientRegistry`.
`user_registry` — 일반 사용자 keypair를 가진 `BackendAIClientRegistry`.

- raw `aiohttp.ClientSession`이나 손으로 만든 auth 헤더를 쓰지 않는다.
- 항상 `BackendAIClientRegistry` 메서드로 API를 호출한다.

## 서버 셋업

통합 테스트는 풀스택 서버(`cleanup_contexts=None`, 모든 컨텍스트 포함)를 쓴다.
`server_factory`에서 `cleanup_contexts`를 `None`에서 바꾸지 않는다 — 통합 테스트는 모든
컨텍스트가 떠 있어야 한다.

## 디렉터리 구조

도메인 기반 하위 디렉터리 구조를 유지한다: `integration/user/`, `integration/session/` 등.
각 하위 디렉터리에 `python_tests()`를 담은 `BUILD`가 필요하다.

## 여기 속하지 않는 것

- service 내부에 대한 유닛 레벨 단언 → `tests/unit/`.
- HTTP 레이어만의 검사(라우팅, auth 데코레이터) → `tests/component/`.
