# v2 개발 방식

## 목표

Go 로 대체하는 manager, agent, storage proxy 를 장기 개발 브랜치 `v2` 에서 개발하고, 대체가 끝난 시점에 `main` 으로 한 번에 반영합니다.

| 목표 | 현재 | 완료 기준 | 관련 이슈 |
|---|---|---|---|
| `v2` 분리와 `main` 동결 | `v2` 브랜치와 `main` 동결 규칙이 없음 | `v2` 가 있고, 새 alembic migration 파일은 CI 가 거부하고 Python 기능 개발은 AGENTS.md 규칙으로 금지 | BAI-1110 |
| 디렉터리 | 저장소 루트에 `go.mod` 와 Go 디렉터리가 없음 | 대체 대상 Python 이 삭제되고 `go.mod`, `cmd/`, `internal/`, `api/`, `migrations/` 가 있음 | BAI-1114(골격), BAI-1112(삭제) |
| 명령, 테스트와 DB schema | go 도구 명령과 DB 테스트 환경이 없음 | go 도구로 lint, 테스트를 실행하고 `v2` 생성 시점의 alembic head schema 가 첫 migration | BAI-1113 |
| `v2` Go CI | base 가 `v2` 인 PR 의 Go CI 가 없음 | `v2` 에는 Go CI 워크플로(`ci.yml`)만 있고 필수 검사는 `ci-gate` 하나 | BAI-1114 |
| 같은 기준 검사 | 언어와 무관한 API 계약 테스트가 없음 | 같은 계약 테스트가 Python 판과 Go 판에서 모두 통과 | BAI-1115 |
| Go 작업 규칙 | `v2` 의 AGENTS.md 가 Go 작업 규칙이 아님 | `v2` AGENTS.md 가 Go 작업 규칙을 담음 | BAI-1116 |
| 전환과 릴리스 | `v2` → `main` 전환 절차와 프리뷰 릴리스 절차가 없음 | 머지 커밋 하나로 반영하고 프리뷰 운영 후 정식 버전 릴리스. 태그 릴리스 워크플로(`release.yml`)가 전체 테스트를 통과해야 빌드 | BAI-1148 |

## 비목표

- client, CLI, webserver, app proxy 의 Go 대체: `v2` 에서 남깁니다.
- account manager, kernel runner, accelerator plugin 의 Go 대체: `v2` 에서 남깁니다.

## 설계

### 브랜치와 `main` 동결

`main` 은 버그 수정만 받고 `v2` 로 동기화하지 않습니다. `v2` 는 대체가 끝난 시점에 `main` 으로 머지 커밋 하나로 반영합니다. manager, agent, storage proxy 를 수정하는 버그 수정 PR 에는 레이블 `require:v2-port` 를 붙이고, 같은 수정을 `v2` 의 Go 코드에 반영합니다.

| 항목 | 규칙 |
|---|---|
| Python 기능 개발 | 멈춤 |
| alembic migration | 멈춤. CI 가 `main` 대상 PR 의 새 alembic migration 파일을 거부 |
| 버그 수정 | 허용. manager, agent, storage proxy 를 수정한 경우 레이블 `require:v2-port` |
| schema 변경이 꼭 필요한 버그 수정 | 사용자 승인 후 레이블 `allow:alembic-migration`. 같은 변경을 `v2` 의 migration 에도 추가 |

### `v2` 의 범위, 모듈, DB schema

`v2` 에서는 Go 로 대체하는 manager(sokovan 포함), agent, storage proxy 의 Python 만 삭제합니다. 빌드, lint, 테스트는 go 도구로 합니다. Pants 는 Go 코드를 다루지 않습니다.

| 항목 | 내용 |
|---|---|
| 지움 | `src/ai/backend/manager`(sokovan 포함), `src/ai/backend/agent`, `src/ai/backend/storage` 의 Python |
| 남김 | client, CLI, webserver, app proxy, account manager, kernel runner, accelerator plugin |
| 모듈 | 루트 단일 모듈 `github.com/lablup/backend.ai`. 바이너리는 `cmd/<이름>/` 마다 따로 빌드 |
| 저장소 루트 | `go.mod`, `cmd/`, `internal/`, `api/`, `migrations/` |
| 개발 도구 | 루트 `go.mod` 의 `tool` 지시어(Go 1.24)에 고정. 지금은 golangci-lint 만. 코드 생성, migration 도구는 API 재작성 BEP 에서 정함 |
| DB schema | 첫 migration 은 `v2` 생성 시점의 alembic head schema. 이후 schema 변경은 `v2` 의 migration 만 |

### 전환 절차

`v2` → `main` 전환은 아래 순서로 합니다. 전환 브랜치에서 `main` 을 머지할 때 수정/삭제 충돌은 삭제로 정리합니다.

| 순서 | 작업 |
|---|---|
| 1 | `main` 을 잠시 동결 |
| 2 | 전환 브랜치에서 `main` 머지. 수정/삭제 충돌은 삭제로 정리하고, `main` 이 새로 추가한 파일로 다시 생긴 삭제한 디렉터리를 다시 삭제. `.github/workflows/ci.yml` 은 `main`(Python)과 `v2`(Go)가 같은 경로라 내용 충돌이 생기며 `v2` 쪽으로 정리 |
| 3 | 충돌 목록으로 버그 수정의 Go 반영(`require:v2-port`)을 대조 |
| 4 | `v2` → `main` PR 을 만들고 머지 커밋으로 머지. 전환 머지 커밋은 지금 `main` ruleset(linear history, squash 만 허용)에 막히므로 전환 때 ruleset 을 바꾸거나 우회 권한으로 머지 |

### CI, 릴리스, 검증

base 가 `v2` 인 PR 은 PR 의 merge commit 의 워크플로를 쓰므로 `v2` 에서 기존 Python CI 워크플로를 삭제하고 Go CI 만 둡니다. 워크플로는 `ci.yml`(PR, `v2` push)과 `release.yml`(태그 릴리스) 두 파일이며 필수 검사는 `ci-gate` 하나입니다. 머지와 릴리스를 분리해 프리뷰 후 정식 버전을 릴리스하고(LTS 는 Python 릴리스 브랜치), 언어와 무관한 API 계약 테스트로 Python 판과 Go 판을 같은 기준으로 검사합니다.

| 시점 | 검사 | 효과 |
|---|---|---|
| pre-commit | `golangci-lint fmt`, `run --fast-only`. `v2` 에는 pre-push hook 이 없음 | 커밋 전 검사 |
| PR | 포맷, lint(golangci-lint), build(`go mod tidy` 차이 포함) | 머지를 막음 |
| PR | `go test -short`, 생성물 차이(`go generate` 후 diff) | 결과만 표시 |
| `v2` push | 커밋마다 전체 테스트(DB, `-race`)와 생성물 차이 검사. 차이가 있으면 다시 생성한 PR 을 엶 | 사후 검사 |
| 태그 릴리스 | 전체 테스트를 통과해야 빌드 | 빌드 조건 |

## 근거 사례

3개월 이력 시뮬레이션과 Bun 의 Zig → Rust 전환입니다.

| 3개월 이력 시뮬레이션 | 결과 | 뒷받침하는 설계 |
|---|---|---|
| 수정/삭제 충돌 | 2,314건 | 전환 절차 2단계: 수정/삭제 충돌을 삭제로 정리 |
| 내용 충돌 | 0건 | 전환 절차 2단계: 수정/삭제 충돌을 삭제로 정리 |
| `main` 이 새로 추가한 파일 | 삭제한 디렉터리로 다시 들어옴 | 전환 절차 2단계: 삭제한 디렉터리를 다시 삭제 |

| Bun PR (oven-sh/bun) | 사실 | 뒷받침하는 설계 |
|---|---|---|
| #30412 `Rewrite Bun in Rust` | 2026-05-08 생성, 2026-05-14 머지. squash 머지 | 대비 사례 |
| #32621 `Remove the .zig porting-reference sources` | 2026-06-25 머지. #30412 의 6주 후이며 옛 Zig 소스 1,270개 파일을 삭제 | 대비 사례 |
| #30733 `http: port fetch TCP keepalive to on_open in lib.rs` | 2026-05-14 머지. #30412 가 #30627 머지 전에 자른 브랜치여서 TCP keepalive 호출이 Rust 로 반영되지 않았고, 이 때문에 `fetch-tcp-keepalive.test.ts` 가 Linux 테스트 job 에서 실패 | 전환 절차 3단계의 충돌 목록 대조와 `require:v2-port` |

대비: Bun 은 squash 머지 후 옛 코드를 6주 후 따로 삭제했습니다. 이 BEP 는 `v2` 에서 미리 삭제하고 머지 커밋으로 반영합니다.

## 영향

- `main` 기여자: 새 alembic migration 파일은 CI 가 거부합니다.
- `main` 기여자: Python 기능 개발은 AGENTS.md 규칙으로 금지합니다.
- `main` 기여자: manager, agent, storage proxy 를 수정한 버그 수정은 `require:v2-port` 를 붙입니다.
- CI: `v2` 에는 Go CI 만 있고, PR 은 포맷, lint, build 만 머지를 막습니다.
- CI: `main` 대상 PR 은 새 alembic migration 파일을 거부합니다.
- DB schema: 전환 후 schema 변경은 `v2` 의 migration 만 사용합니다.
- 릴리스: 머지 후 프리뷰를 거쳐 정식 버전을 릴리스합니다. LTS 는 Python 릴리스 브랜치가 맡습니다.

## 구현 순서

1. `main` 동결 규칙과 `v2` 생성(BAI-1110): 레이블 2종, 새 alembic migration 파일 거부 CI
2. Go 모듈 골격과 Go CI(BAI-1114): `go.mod`, 최상위 디렉터리, `ci.yml`
3. 대체 대상 Python 삭제(BAI-1112)
4. 명령과 DB 테스트 환경(BAI-1113)
5. API 계약 테스트 틀(BAI-1115), `v2` AGENTS.md 의 Go 작업 규칙(BAI-1116): 나란히 진행
6. 릴리스 CI(BAI-1148): `release.yml`
7. 전환과 릴리스: 전환 절차대로 `v2` → `main` 머지 커밋, 프리뷰 운영 후 정식 버전

## 참고

- Bun: oven-sh/bun #30412, #32621, #30733
