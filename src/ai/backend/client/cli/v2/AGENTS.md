# CLI v2 — 가드레일

## 명령 계층

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `cli/v2/{entity}/commands.py` — 사용자 대면 명령(인증된 모든 사용자)
- `cli/v2/admin/{entity}.py` — admin 전용 명령(superadmin 필요)
- `cli/v2/my/{entity}.py` — self-service 명령(현재 사용자 본인 리소스)

## admin / non-admin / my 배치

**admin 전용 연산은 `{entity}/commands.py`가 아니라 `admin/{entity}.py`에 둔다.**

- admin 전용 엔티티(Domain, ContainerRegistry 등)의 `create`, `update`, `delete`, `purge` → `admin/`
- 스코프 없는 `search`(전체 시스템 조회) → `admin/`
- ID로 `get`(인증된 모든 사용자) → `{entity}/commands.py`
- scoped search → 스코프를 필수 인자로 받아 `{entity}/commands.py`

**scoped search CLI 패턴** (검토 중 — SDK `scoped_search` 방향에 맞춰 바뀔 수 있음):
- 현재: 명령 이름이 스코프를 반영한다 — `./bai session project-search {project_id}`.
- 스코프 ID는 옵션 플래그가 아니라 필수 위치 인자.
- REST `POST /v2/{entity}/{scope_type}/{scope_id}/search`에 매핑.

**self-service 연산(서버 `my_` 접두)은 `my/{entity}.py`에 둔다.**

- 현재 사용자 본인 리소스를 다루는 self-service 연산 → `my/`
- 서버 `my_` 접두 API와 `/v2/{entity}/my/` REST 엔드포인트에 매핑(`my`는 스코프 한정자, 엔티티가 앞)
- 예) `./bai my keypair search`, `./bai my keypair issue`

같은 연산에 admin/non-admin 변형이 둘 다 있으면(권한이 아니라 동작이 다름), admin은 `admin/`에,
non-admin은 `{entity}/commands.py`에 둔다.

## SDK v2 통합

- CLI는 SDK v2 메서드(`registry.{entity}.method()`)를 호출한다 — REST 직접 호출 금지.
- SDK 클라이언트: `client/v2/domains_v2/{entity}.py`
- SDK 레지스트리: `client/v2/v2_registry.py`
- 새 SDK 도메인 클라이언트는 `V2ClientRegistry`에 `@cached_property`로 등록한다.

## 연산 네이밍

표준 6개 연산은 고정 명령 이름을 쓴다: `create`, `get`, `search`, `update`, `delete`, `purge`.
6-op 패턴 밖의 연산만 다른 이름을 쓴다:
- `enqueue`, `terminate`(세션 라이프사이클)
- `revision add`, `revision activate`, `revision current`(deployment revision)
- `login`, `logout`(auth)

## 명령 입력 스타일

- **기본:** 각 필드마다 개별 `--option` 플래그.
- **보조:** 깊게 중첩된 구조(예: revision config)는 단일 옵션으로 JSON 문자열이나 `@file` 경로를 받는다
  (예: `--config '{"cluster_config": ...}'` 또는 `--config @revision.json`).
- create/update에 raw JSON을 위치 인자로 **절대** 쓰지 않는다.
- get/delete/purge는 엔티티 식별자(UUID, 이름)를 위치 인자로.
- search 필터는 `--option` 플래그로: `./bai admin domain search --name-contains foo`
- JSON 출력은 `print_result()` 헬퍼를 쓴다.
- DTO 클래스는 명령 함수 안에서 lazy import한다.

## 새 엔티티 추가

1. 사용자 대면 명령 + `__init__.py`를 담은 `cli/v2/{entity}/commands.py` 생성
2. admin 전용 명령 `cli/v2/admin/{entity}.py` 생성
3. self-service 명령 `cli/v2/my/{entity}.py` 생성(해당 시)
4. `cli/v2/__init__.py`에 사용자 대면 그룹 등록
5. `cli/v2/admin/__init__.py`에 admin 그룹 등록
6. `cli/v2/my/__init__.py`에 my 그룹 등록(해당 시)
7. `/bai-cli` 스킬의 Entity-Command Reference에 새 엔티티·명령을 등록한다(테스트가 무엇을 실행할지 알 수 있도록).
