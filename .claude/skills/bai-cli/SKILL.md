# ./bai CLI 사용 가이드

Backend.AI **v2 CLI**(`./bai`)로 API 엔드포인트를 테스트·검증하고 리소스를 관리하는 가이드.

**중요:**
- `./bai`는 v2 REST API CLI다. 레거시 v1 CLI(`backend.ai` / `./backend.ai`)와 별개다.
- v1 CLI 명령을 쓰지 않는다. 모든 테스트·검증은 `./bai`로 한다.
- **`./bai` 명령 실행 전, 아래 Entity-Command Reference에서 명령 존재를 확인한다.** 추측·날조 금지, CLI 소스 탐색 금지.
- 명령 트리는 `--help`로 검증한다(서버 없이 동작): `./bai {entity} --help`, `./bai admin {entity} --help`, `./bai my {entity} --help`.

### v1 → v2 용어

| v1 (레거시, 사용 금지) | v2 (`./bai`) |
|--------------------------|-------------|
| `group` | `project` |
| `backend.ai vfolder list` | `./bai vfolder my-search` |
| `backend.ai admin vfolders` | `./bai vfolder admin-search` |
| `backend.ai ps` | `./bai my session search` |

---

## Entity-Command Reference

문법: `./bai [admin|my] {entity} [{sub-entity}] {command} [options]`

각 엔티티는 접근 레벨별로 표기한다 — **user**(사용자 대면) / **admin**(superadmin 전용) / **my**(본인 리소스).
"(빈 그룹)"은 명령이 없는 placeholder 그룹이다(예: `./bai agent`는 비어 있고 실제 명령은 `./bai admin agent`).
옵션은 `--help`로 확인한다.

### Core

- **domain**: user(get) · admin(search, create, update, delete, purge)
- **user**: user(get, create, update, delete, search) · admin(create, delete, search)
- **project**: user(get, assign-users, unassign-users · sub role: search) · admin(search, create, update, delete, purge)
- **agent**: user(빈 그룹) · admin(search, total-resources)
- **image**: user(빈 그룹) · admin(search, forget, purge, update · sub alias: create, remove, search)
- **session**: user(enqueue, get, logs, project-search, start-service, shutdown-service, terminate, update) · admin(search · sub kernel: search) · my(search)

### Compute & Serving

- **deployment**: user(create, get, update, delete, project-search, chat) · admin(search) · my(search)
  - user sub: access-token(create, get, search, delete, bulk-delete), auto-scaling-rule(create, get, search, update, delete, bulk-delete), replica(search), revision(add, get, current, activate, search), revision-preset(get, search), options(get, replace), chat-cache(show, clear), chat-config(set, show, clear), chat-history(show, clear), policy(빈 그룹)
  - admin sub: policy(search), replica(search), revision(search, refresh), revision-preset(create, get, search, update, delete)
- **model-card**: user(project-search, get, deploy, available-presets) · admin(search, get, create, update, delete, bulk-delete, scan)
- **service-catalog**: user(빈 그룹) · admin(search)
- **runtime-variant**: user(get, search) · admin(get, search, create, update, delete, bulk-delete)
- **runtime-variant-preset**: user(get, search) · admin(get, search, create, update, delete)
- **scheduling-history**: sub session / deployment / route — 각 (search, search-scoped)
- **scheduling-handler**: admin(list)

### Storage

- **vfolder**: user(my-search, project-search, admin-search, create, project-create, get, upload, download, delete, purge, restore, ls, mkdir, mv, rm, clone, deploy, bulk-delete, bulk-purge)
- **vfs-storage**: user(create, get, search, list-all, update, delete)
- **storage-namespace**: user(register, unregister, search, get-by-storage)
- **object-storage**: user(create, get, search, update, delete)
- **storage-host**: my(permissions)

### Registries & Artifacts

- **container-registry**: user(빈 그룹) · admin(search, create, update, delete)
- **artifact**: user(get, update, delete, restore · sub revision: get, approve, reject, cancel-import, cleanup) · admin(search)
- **artifact-registry**: user(get)
- **huggingface-registry**: user(create, get, search, update, delete) — admin 변형 없음
- **reservoir-registry**: user(create, get, search, update, delete)

### Access Control & Auth

- **rbac**: sub assignment(assign, revoke, search), entity(search), permission(search),
  invitation(create, accept, reject, cancel, my-search, my-sent-search, role-search),
  role(create, get, search, update, delete, project-search, add-permission, remove-permission, replace-permission)
- **role**: my(search)
- **role-preset**: admin(create, get, search, update, delete, purge, restore, permission-add, permission-remove, permission-search)
- **invitation**: admin(search)
- **keypair**: admin(create, get, search, update, delete · sub ssh: register, get, delete) · my(issue, revoke, search, update, switch-main)
- **login-history**: admin(search) · my(search)
- **login-session**: admin(search, revoke) · my(search, revoke)
- **login-client-type**: user(get) · admin(search, create, update, delete)

### Resource Management

- **resource-group**: user(빈 그룹) · admin(search, get, create, delete, resource-info, default-options, default-session-options, allow-domains, allowed-domains, allow-projects, allowed-projects, allow-for-domain, allowed-for-domain, allow-for-project, allowed-for-project)
- **resource-allocation**: user(project-usage, resource-group-usage) · admin(domain-usage, effective) · my(effective, keypair-usage)
- **resource-preset**: admin(search, get, create, update, delete, check-availability)
- **resource-policy**: admin(sub keypair / project / user — 각 create, get, search, update, delete) · my(keypair, user)
- **resource-slot**: sub slot-type(search), agent-resource(search), allocation(search)
- **resource-usage**: sub domain(search), project(search), user(search)

### Monitoring & Audit

- **audit-log**: user(search)
- **fair-share**: sub domain / project / user — 각 (get, search)
- **notification**: sub channel(get, search, delete), rule(get, search, delete)
- **prometheus-query-definition**: user(get, search, execute) · admin(create, update, delete, preview)
- **prometheus-query-definition-category**: user(get, search) · admin(create, delete)
- **app-config**: user(get-domain, get-user, get-merged, delete-domain, delete-user)
- **export**: admin(list-reports, get-report, audit-logs, keypairs, projects, sessions, sessions-by-project, users, users-by-domain) · my(keypairs, sessions)

### 유틸리티 (엔티티 아님)

`login`, `logout`, `config`, `gql` — 루트의 단일 명령.

> 새 CLI 명령을 추가하면 이 Reference도 갱신한다(`client/cli/v2/AGENTS.md`의 "새 엔티티 추가" 참고).

---

## 셋업 (Webserver 세션 — 권장)

```bash
./bai config set endpoint http://127.0.0.1:8090
./bai config set endpoint-type session
./bai login
# User ID: admin@lablup.com
# Password: (admin 비밀번호)
./bai config show
```

비대화 환경(CI, Claude Code):

```bash
BACKEND_USER=admin@lablup.com BACKEND_PASSWORD=wJalrXUt ./bai login
```

세션 쿠키는 `~/.backend.ai/session/cookie.dat`에 저장된다.

### Direct API (대안)

웹서버 없이 매니저에 직접 접근(HMAC 서명 인증):

```bash
./bai config set endpoint http://127.0.0.1:8091
./bai config set endpoint-type api
./bai config set access-key AKIAIOSFODNN7EXAMPLE
./bai config set secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
./bai config show
```

설정은 `~/.backend.ai/config.toml`, `credentials.toml`에 저장된다.

## 명령 패턴

```
./bai [admin|my] {entity} [{sub-entity}] {command} [options]
```

- `admin` — superadmin 전용 연산
- `my` — self-service(현재 사용자 본인 리소스)
- 엔티티 이름은 **단수**(domain, user, agent)
- sub-entity는 Click 서브그룹(revision, channel, role 등)

표준 6개 연산: `create`, `get`, `search`, `update`, `delete`, `purge`(엔티티에 따라 일부만).
특수 연산: `enqueue`/`terminate`(session), `revision add`/`revision activate`(deployment), `login`/`logout`.

## CLI 입력 스타일

- **기본:** 필드마다 개별 `--option` 플래그.
- **보조:** 복잡한 중첩 구조는 JSON 문자열이나 `@file` 경로(예: `--initial-revision`, `--config`).
- create/update에 raw JSON을 위치 인자로 쓰지 않는다(일부 admin 명령 예외: `admin domain create`).
- get/delete/purge는 엔티티 식별자(UUID, 이름)를 위치 인자로.

## 검색 패턴

```bash
# admin 검색 — 전체 시스템 (superadmin 전용)
./bai admin {entity} search --limit 5

# project 스코프 검색 — 스코프 ID는 위치 인자(옵션 아님)
./bai {entity} project-search {project_id} --limit 5

# self-service 검색 — 본인 리소스
./bai my {entity} search --limit 5
```

옵션·필터는 엔티티마다 다르므로 `./bai {entity} {command} --help`로 확인한다.

### --order-by 문법

`field:direction`로 다중 정렬:

```bash
./bai admin user search --order-by created_at:desc --order-by username:asc
```

## 네이밍 규약

- CLI `--order-by`는 DTO `order` 필드에 매핑(전 엔티티 공통).
- CLI `--kebab-case` 옵션은 DTO `snake_case` 필드에 매핑(Click 표준).
- 스코프 검색: 스코프 ID는 `--scope-*` 옵션이 아니라 **위치 인자**.

## Raw GraphQL

`./bai gql`(`./bai admin gql` 아님)는 raw GraphQL 쿼리를 보낸다. GQL 스키마 변경 테스트나 REST CLI가 없을 때 유용:

```bash
./bai gql '{ domain(name: "default") { name } }'
./bai gql --v2 '{ myKeypairs(first: 5) { count edges { node { accessKey } } } }'
./bai gql -f query.graphql
./bai gql --var limit=5 '{ keypair_list(limit: $limit) { items { access_key } } }'
```

- `--v2`: Strawberry v2 스키마 대상(direct API 모드에서만 필요, 세션 모드는 둘 다 제공)
- `--var key=value`: 쿼리 변수(반복 가능)
- `-f file`: 파일에서 쿼리 읽기
- stdin: `echo '{ ... }' | ./bai gql`

## 자주 쓰는 명령

```bash
# admin 검색 + 필터 (superadmin 전용)
./bai admin domain search --limit 5 --name-contains default
./bai admin user search --status active --order-by created_at:desc
./bai admin agent search --limit 10
./bai admin image search --name-contains python
./bai admin session search --limit 5

# 단일 엔티티 조회
./bai domain get default
./bai user get <uuid>

# 서브 엔티티 연산
./bai admin deployment revision search
./bai rbac role search
./bai notification channel search
./bai scheduling-history session search --limit 10
```

## 테스트 워크플로

### 전제

```bash
./bai config show   # endpoint-type 확인
./bai login         # 세션 만료 시 로그인
```

### 서버 코드 수정 후

로컬 개발은 서비스를 먼저 재시작한다 — `/local-dev` 스킬 참고.

```bash
# 1. 기본 연결 확인
./bai admin domain search --limit 1
./bai domain get default

# 2. 수정한 엔티티 테스트 (해당 레벨에 맞는 명령으로)
#    user 대면이면 ./bai {entity} ..., admin 전용이면 ./bai admin {entity} ...
./bai admin {entity} search --limit 1
./bai {entity} get {id}

# 3. 권한 경계 테스트
./bai admin {entity} search    # admin은 성공
# 일반 사용자로 전환 후 같은 명령 → 403 실패해야 함
```

명령 후에는 Grafana MCP로 런타임 동작을 확인한다 — `/observability` 참고.
CLI 응답에 안 드러나는 에러를 잡으려면 Loki(`{service_name="manager"} |= "error"`)를,
요청 카운트 확인은 Prometheus(`backendai_api_request_count`)를 본다.

### 일반 사용자로 테스트

기본 계정은 `fixtures/manager/example-users.json`.

```bash
# 일반 사용자 세션 로그인
BACKEND_USER=user@lablup.com BACKEND_PASSWORD=C8qnIo29 ./bai login

# 성공해야 함 (user 대면)
./bai domain get default

# 403 실패해야 함 (admin 전용)
./bai admin domain search --limit 1
```

테스트 후 admin 자격증명으로 되돌린다.

## Smoke 테스트 스크립트

모두 admin 자격증명에서 실행. 각 명령이 JSON을 반환하면 OK.

```bash
for cmd in \
  "admin domain search --limit 1" \
  "domain get default" \
  "admin user search --limit 1" \
  "admin project search --limit 1" \
  "admin agent search --limit 1" \
  "admin image search --limit 1" \
  "admin session search --limit 1" \
  "admin resource-group search --limit 1" \
  "audit-log search --limit 1" \
  "rbac role search --limit 1"; do
  echo -n "$cmd: "
  ./bai $cmd 2>&1 | python3 -c "import sys,json;json.load(sys.stdin);print('OK')" 2>&1 || echo "FAIL"
done
```

## CLI 명령이 없을 때

엔티티/연산의 CLI 명령이 위 Reference에 없으면:

1. 그 명령은 **미구현**이다.
2. **사용자에게 보고**: "{entity} {operation}은 CLI로 제공되지 않습니다. 구현이 필요합니다."
3. 임시 우회로 GraphQL 가능 연산은 `./bai gql` 시도.
4. CLI 옵션을 추측하거나 명령을 날조하지 않는다 — 시간 낭비·오류 유발.

## 관련 스킬

- `/local-dev` — CLI 테스트 전 로컬 서비스 재시작
- `/observability` — CLI 테스트 후 Grafana MCP로 로그/메트릭 확인
- `/cli-sdk-guide` — 새 CLI 명령 구현
