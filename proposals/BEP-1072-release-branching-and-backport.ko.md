# 릴리스 브랜치 격리와 백포트 자동화

## 관련 이슈

- Epic **BA-7049**, 이 BEP **BA-7050**
- 참고(확장하지 않음): `src/ai/backend/manager/models/alembic/README.md` - migration 백포트 전략

## 1. 목표

`main` 이 개발 브랜치와 현행 릴리스 버전을 겸하고 있어서, 릴리스 버전을 기능 merge 와 분리해 안정화할 수 없다. 백포트 대상은 손으로 지정한 milestone 에 의존하고, 백포트가 실패하면 PR 이 아예 생성되지 않아 무엇이 빠졌는지 알 방법이 없다.

이 BEP 는 릴리스 절차를 **세 동작**으로 다시 정의한다. rc 릴리스와 버전 브랜치 분기, rc 기간의 fix 백포트와 검증, 그리고 변경 기록을 `main` 에 반영하는 최종 릴리스다.

**용어.** **버전 브랜치**는 브랜치가 되는 `YY.S` 단위(`26.8`)이고, `<version>` 으로 적고 다음 것은 `<next>` 로 적는다. **릴리스 제목 블록**은 변경 기록 파일에서 `## <version>.<patch> (<date>)` 블록 하나로, 다음 `##` 까지를 말한다. towncrier 한 번이 생성하는 것과 정확히 같다.

**범위 밖**

- 버전 등급(Edge/LTS)과 지원 기간 정의. 그것은 지원 정책 문서가 맡는다. 여기서는 **유지 중인 버전 목록**만 다룬다.
- 백포트의 자동 충돌 해결과 `Fixes:` trailer. CI 에서 백포트 범위를 추론하는 것은 미루는 것이 아니라 처음부터 기각한다. 3.(b)를 참고한다.
- 버전 브랜치에서 `main` 으로 **코드**를 되돌리는 일. 브랜치에만 있는 코드 commit 은 0으로 측정됐으므로 원칙만 적고 workflow 는 생성하지 않는다.
- 릴리스 아티팩트에서 WebUI bundle 을 제거하는 일. 지금은 아티팩트 안에 담겨야 하므로 3.(d)는 bundle 을 **언제** 고정하는지만 분리하고 위치는 그대로 둔다.
- Alembic 백포트 정책과 버전 번호 체계 변경. milestone 은 릴리스 계획용으로 남는다. 백포트 결정에서만 뺀다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다. 측정값(2026-07-28): `.0` 간격 17~31일, `rc1`→`.0` 1~5일, 26.4 분기 뒤 6주 동안 브랜치 commit 52개 = 자동 백포트 42개 + 수동 6개 + 릴리스 4개, **브랜치에만 있는 코드 commit 0개**.

### 2.1 브랜치 분기와 rc

| | 항목 |
|---|---|
| ✅ | 브랜치는 다음 버전이 시작될 때만 분기한다. 26.4 의 분기점은 `release: 26.4.4` commit 이다 |
| ✅ | rc 릴리스는 버전 브랜치 없이 `main` 의 tag 로 나간다(`26.4.0rc1` 등) |
| ✅ | tag 생성과 브랜치 생성은 수동이다. `daily-workflows.rst` 가 손으로 실행하는 git 명령으로 적어 둔다 |
| ➕ | **기능이 끝나면 `main` 에서 rc1 을 릴리스하고, 그 merge commit 에 tag 를 붙이면서 같은 commit 에서 버전 브랜치를 분기한다. 한 동작이다.** 분기 시점에 브랜치의 commit 은 0개다 |
| ➕ | 그 동작을 release PR merge 시 `merge_commit_sha` 를 기준으로 자동화한다 |

### 2.2 버전 값

| | 항목 |
|---|---|
| ✅ | `VERSION`(루트에 있고 10개 패키지에 symlink 된다)이 wheel metadata 와 표시 버전을 모두 정한다 |
| ✅ | `release.sh` 가 최종 릴리스에서 `NEXT_RELEASE_VERSION`(`meta.py`, 참조 154곳)을 고정하고 그 뒤에 올린다. 둘 다 `main` 에서 한다 |
| ➕ | `VERSION` = **그 tree 가 마지막으로 릴리스한 버전**. 릴리스 commit 만 갱신하므로 **항상 tag 와 일치한다** |
| ➕ | 고정과 NEXT 올리기를 **분기(rc 릴리스) PR** 에 합치고, 손이 아니라 script 가 수행한다. 브랜치는 고정된 결과를 그대로 가진다 |

### 2.3 백포트 대상 결정

| | 항목 |
|---|---|
| ✅ | `backport.yml` 이 PR 의 **milestone** 을 읽고, 같은 이름의 브랜치가 있는 것만 남긴 뒤 그 이상인 모든 버전으로 펼친다 |
| ✅ | 지금 milestone 은 `Backlog/26.5/26.4/25.15` 이고 `main` 은 26.8 을 개발한다. 그래서 `26.5` 가 의도치 않은 opt-out 으로 동작한다 |
| ➕ | milestone 을 제거한다. **PR 제목 접두사와 설명의 `Backport:` trailer** 로 정하고, `.github/maintained-versions.yml` 과 대조한다. label 은 사용하지 않는다 |
| ➕ | 정해진 집합의 모든 대상을 시도한다. 미리 걸러 내지 않으므로 적용할 수 없는 fix 는 조용히 건너뛰지 않고 draft PR 로 드러난다(3.(b)) |

### 2.4 백포트 실패 처리

| | 항목 |
|---|---|
| ✅ | cherry-pick 이 `--strategy-option=theirs` 를 사용하므로 충돌 hunk 를 조용히 덮어쓴다 |
| ✅ | 실패하면 원래 PR 에 한 줄 comment 를 남기고 job 을 끝낸다. **PR 이 생성되지 않으므로 추적할 수 없다** |
| ✅ | 실제 merge commit 에 `Backported-from/to/of` trailer 가 없다(26.4 전체에서 1건) |
| ➕ | `-X theirs` 를 제거한다. 충돌하면 **충돌 marker 를 그대로 commit 하고 draft PR** 과 `pending:backport` 를 생성한다 |
| ➕ | trailer 를 수정해 merge commit body 에 담기게 한다 |

### 2.5 변경 기록

| | 항목 |
|---|---|
| ✅ | 4267줄짜리 `CHANGELOG.md` 하나. towncrier 는 늘 같은 지점에 넣으므로 두 버전이 릴리스되면 충돌이 확정된다 |
| ✅ | fragment 가 없어도 **빈 릴리스 제목 블록이 생성된다.** `extract-release-changelog.py` 가 그것을 찾아 실패 없이 **빈 릴리스 노트**를 내보낸다 |
| ✅ | rc 제목 블록은 릴리스 시 최종 블록으로 합쳐진다. `26.4.4rc1`~`rc9` 를 tag 했는데도 `CHANGELOG.md` 에 `## ...rc` 제목은 0개다 |
| ➕ | **버전 브랜치별 파일**(`CHANGELOG-<version>.md`). `release.sh` 는 `[tool.towncrier]` 를 복사하고 `filename` 만 덮어쓰는 임시 config 로 실행한다 |
| ➕ | 소비할 fragment 가 없으면 towncrier 를 건너뛴다. prerelease 면 블록을 찾기 전에 rc 접미사를 제거한다 |
| ➕ | 파일은 rc 부터 완전한 릴리스 노트로 읽혀야 하고, 최종 릴리스가 그것을 하나로 합치며, patch 릴리스는 **그 릴리스로 백포트된 fix 만** 기록한다 |

### 2.6 WebUI bundle 과 GraphQL schema

| | 항목 |
|---|---|
| ✅ | 빌드된 WebUI bundle 은 이 저장소에 commit 한 상태이고(`src/ai/backend/web/static/`, 4718개 파일), `resources(sources=["static/**/*"])` 로 wheel 에 담긴다 |
| ✅ | `release.sh <version> [webui_version]` 이 **릴리스 commit 안에서** bundle 을 고정한다. `static/` 을 건드린 최근 commit 은 모두 `release:` commit 이다 |
| ✅ | WebUI 는 `docs/manager/graphql-reference/` 를 기준으로 빌드하고, 모든 tag(rc 포함)가 이미 `supergraph.graphql` 을 GitHub Release asset 으로 배포한다 |
| ✅ | 버전 브랜치에서 schema 는 덜 움직이지만 움직인다. `26.4` 의 55개 commit 이 `docs/manager/graphql-reference/` 를 건드린 횟수는 0회인데, **26.8 은 rc1 이후 schema 변경이 7건**이었다. 6건은 추가, 1건은 breaking(`DeleteResourceGroupPayload.id` `String!`→`UUID!`, #13277)이다 |
| ✅ | `graphql-inspector` job 은 `schema.graphql`(graphene v1)만 비교한다. 7건 모두 v2 였으므로 전부 그 시야 밖이었고, breaking 1건이 merge 됐다 |
| ➕ | 이것을 **규칙**으로 정한다. rc1 tag 부터 버전 브랜치는 schema 에 **추가**할 수 있지만 깨뜨릴 수는 없다. 추가는 허용하고 breaking 은 차단한다 |
| ➕ | `graphql-inspector` 를 `supergraph.graphql`(v1+v2 상위 집합)로 실행해 규칙이 두 subgraph 를 포괄하게 한다. `main` 의 같은 구멍도 이것으로 닫힌다 |
| ➕ | bundle 을 릴리스 commit 이 아니라 **독립 PR** 에서 고정한다. `release.sh` 에서 `webui_version` 을 제거한다 |

## 3. 구현 설계

**핵심 흐름**: 기능 완료 → `main` 에서 rc1 릴리스(고정 + NEXT 올리기 + towncrier) → 같은 commit 에 tag 를 붙이고 버전 브랜치를 분기 → rc 기간에 fix 백포트 → 브랜치에서 `.0` 릴리스 → 버전 변경 기록을 `main` 으로 복사.

### (a) rc 릴리스와 버전 브랜치 분기

| # | 위치 | 동작 |
|---|---|---|
| 1 | `main` PR `release: <version>.0rc1` | `VERSION` → `<version>.0rc1` / freeze(`<version>.0`) + `pants fix/fmt` / **NEXT → `<next>.0`** / sample 과 schema 재생성 / towncrier 소비(`--version <version>.0`) → `CHANGELOG-<version>.md` 생성 / `maintained-versions.yml` 에 `<version>` 등록(`<version>.0rc1` 대상 자체에서 릴리스 script 가 수행한다. `--lts` 는 장기 지원 line 을 표시한다) |
| 2 | `main` | merge 되면 merge commit 에 `<version>.0rc1` tag 를 붙이고 **같은 commit 에** `<version>` 브랜치를 생성한다. **한 동작이고 브랜치의 commit 은 0개다** |

**분기는 `main` 에서 rc1 을 릴리스하는 행위이고, PR 하나로 끝난다.** 브랜치는 `VERSION` 과 fragment pool 이 이미 올바른 상태를 그대로 가지므로 건드릴 것이 없다. rc1 tag 는 `main` 과 버전 브랜치의 공통 조상이고, rc1 은 브랜치에서 다시 tag 하지 않는다.

1번 row 는 손이 아니라 script(`cut-release-branch.sh`)가 생성한다. `freeze_release_version.py` → `pants fix/fmt` → `bump_next_release_version.py` → sample/schema 재생성 → towncrier → 등록을 실행한 뒤 PR 을 연다. 2번 row 는 release PR merge 시 `merge_commit_sha` 를 읽는 workflow 이므로 tag 와 브랜치가 구조적으로 같은 commit 을 참조한다.

> tag 는 백포트 PR 에 이미 사용하는 PAT 로 push 해야 한다. 기본 `GITHUB_TOKEN` 으로 생성한 ref 는 다른 workflow 를 트리거하지 않고, `ci.yml` 의 `make-final-release`(빌드, GitHub Release, PyPI upload)가 tag push 로 실행된다.

분기 PR 에서 고정하고 브랜치에서는 하지 않는 이유는 둘이다. `freeze_release_version.py` 는 import 를 삭제하고 `pants fix/fmt` 를 실행하므로 브랜치에서 하면 두 tree 가 갈라져 나중 cherry-pick 충돌이 늘어난다. 그리고 분기 시점의 `main` 코드는 `<version>.0` 에서 처음 배포되므로 `added_version=<version>.0` 이 의미상 맞다.

NEXT 올리기도 같은 PR 에서 일어나므로 브랜치는 자기가 릴리스하지 않는 버전인 `<next>.0` 을 그대로 가진다. 이것은 실제로 드러난다. 26.8 은 rc1 이후 `feat:` commit 이 3개였고, 셋 다 26.8.x 로 배포되면서 `added_version=26.9.0` 을 달고 있었다. 그래서 버전 브랜치의 규칙은 `main` 의 규칙과 반대다. 브랜치가 배포할 버전을 literal 로 적고 `NEXT_RELEASE_VERSION` 은 사용하지 않는다. CI 는 버전 브랜치 PR 에서 새로 추가된 참조를 거부하고 이미 있던 참조는 그대로 둔다.

버전 변경 기록 파일은 stub 으로 미리 생성하지 않는다. rc1 의 towncrier 가 생성하고, 그 시점에 이미 완전한 릴리스 노트로 읽혀야 한다.

### (b) rc 기간의 fix 백포트와 검증

rc 기간은 명목상 **1주**다(기능 검증과 test 보강에 충분하다).

| # | 동작 |
|---|---|
| 1 | 대상을 정한다. 접두사가 기본값을 고르고(`fix:` → `maintained-versions.yml` 의 모든 버전, 그 밖 → 없음), 설명의 `Backport:` trailer 가 그것을 **대체**하며 특정 버전이나 `none` 을 적는다. merge 된 PR 에 `/backport <version>` 을 남기는 것이 이후에 추가하는 방법이다 |
| 2 | **모든** 대상에 cherry-pick 을 수행한다. 성공하면 auto-merge 를 건 PR 을, 충돌하면 **draft PR** 과 `pending:backport` 를 생성한다 |

오래된 버전에 들어간 fix 는 살아 있는 모든 상위 버전에도 적용된다(그래야 upgrade 때 버그가 다시 나타나지 않는다).

**모든 대상을 시도하고, 미리 거르지 않는다.** CI 는 fix 가 특정 버전에 속하는지 알아내려 하지 않는다. 그것은 추론만 가능하고(변경된 hunk 를 blame 해 도입 commit 을 찾고 `git tag --contains` 를 본다), 추론은 refactor 와 파일 이동을 거치면 믿을 수 없으며, 그것을 근거로 대상을 제거하면 이 BEP 가 없애려는 조용한 건너뛰기 그 자체가 된다. 따라서 적용할 수 없는 cherry-pick 은 숨길 실패가 아니라 신호다. draft PR 에서 skill 이 결정한다. 충돌을 해결하거나, 그 버전에 fix 가 필요 없다고 판단해 이유를 기록하고 닫는다.

**실패도 결과로 기록한다.** draft PR 로 남겨 두면 버전별 미완 목록이 PR 목록으로 보이고, 같은 skill 이 분류하고 정리한다. 버전 브랜치에 required-checks ruleset 을 걸어 auto-merge 가 CI 를 건너뛰지 못하게 한다. `ci.yml` 의 push filter 가 이미 버전 브랜치 패턴을 담고 있으므로 workflow 변경은 필요 없다.

검증이 더 필요하면 브랜치에서 `<version>.0rc2` 를 분기한다.

### (c) 최종 릴리스와 변경 기록의 `main` 반영

| # | 위치 | 동작 |
|---|---|---|
| 1 | 브랜치 PR `release: <version>.0` | `VERSION` → `<version>.0`, 소비할 fragment 가 있으면 towncrier 실행, rc 내용을 최종 릴리스 제목 블록으로 합침 |
| 2 | 브랜치 | `<version>.0` tag |
| 3 | `main` PR(자동) | `git checkout origin/<version> -- CHANGELOG-<version>.md`. **파일 하나를 복사한다** |

patch 릴리스(`<version>.1` 이후)도 같은 경로를 타고, 그 제목 블록은 **그 릴리스로 백포트된 fix 만** 기록한다. patch 릴리스는 다른 것을 배포하지 않는다. 3번 row 의 복사는 모든 최종 tag 에서 실행하고 prerelease 에서는 하지 않는다.

복사로 충분한 이유는 다음과 같다. 버전 파일은 그 브랜치만 소유하고, `main` 은 분기 때 생성한 뒤 그 파일을 건드리지 않으므로 merge 할 대상이 없다. 멱등이므로 다시 실행해도 안전하고, 파일이 버전 브랜치별로 있으므로 여러 버전의 동시 릴리스가 충돌할 수 없다. 접두사가 `release:` 이므로 그 자체가 (b)의 대상이 아니다. loop 가 없다.

이 PR 은 `changes/` 를 건드리지 않는다. **각 tree 가 자기 fragment pool 을 자기 릴리스로 비운다.** `main` pool 은 분기(rc1)가, 브랜치 pool 은 그 브랜치의 릴리스가 비운다. 브랜치가 소비한 fragment 는 `main` pool 에 남아 다음 분기에 `<next>` 의 노트로 다시 소비된다. 같은 fix 가 두 버전의 노트에 나오는 것은 예상된 일이다.

### (d) WebUI bundle 과 schema 계약

bundle 은 릴리스 아티팩트 안에 담겨야 하므로 두 저장소를 packaging 으로 분리할 수 없다. 대신 시간으로 분리한다. WebUI 는 schema 를 **일찍**(분기 시점에) 필요로 하고 이 저장소는 bundle 을 **늦게**(최종 릴리스에) 필요로 하며, rc 기간이 정확히 그 간격이다.

| 주체 | 약속 |
|---|---|
| backend.ai | rc1 tag 에서 `supergraph.graphql` 을 릴리스 asset 으로 배포하고, 그 뒤 그 버전 브랜치에서 schema 에 **breaking change 를 일으키지 않는다** |
| WebUI | 그 asset 을 기준으로 빌드해 bundle 을 릴리스한다 |
| backend.ai | 나온 bundle 을 릴리스 commit 이 아니라 **독립 PR** 로 받는다 |

**계약은 전체 동결이 아니라 additive only 다.** 전체 동결이 원래 의도였지만 브랜치는 실제로 schema 를 변경한다. 26.8 rc1 이후 7건 중 6건이 추가, 1건이 breaking 이었다. 추가 변경은 WebUI 에 비용이 없다. 새 field 를 사용하지 않을 뿐이다. 그래서 추가를 차단하면 해로운 1건을 잡으려고 무해한 6건을 거부하게 된다. WebUI 가 필요한 보장은 rc1 asset 의 모든 것이 남는다는 점이다. **rc1 asset 이 WebUI 가 의존할 수 있는 schema 의 하한**이고, 그 버전의 최종 schema 가 아니다.

강제는 기존 `graphql-inspector` job 이 맡고, 대상을 `schema.graphql` 에서 `supergraph.graphql` 로 변경한다. 26.8 에 merge 된 breaking change(#13277)는 v2 전용이라 설정된 job 에 보이지 않았다. supergraph 는 두 subgraph 의 상위 집합이므로 입력 하나를 변경하면 v1 과 v2 를 한 번에 포괄한다. merge 차단은 그대로 둔다. job 의 check run 이 required status check 이고, action 에 내장된 `approved-breaking-change` label 이 탈출구다. 그 check 를 버전 브랜치 ruleset 에 required 로 등록하는 일은 BA-7134 다.

**bundle 고정은 릴리스와 분리한다.** `release.sh` 는 `webui_version` 인자를 제거한다. bundle 은 WebUI 가 배포할 때마다 `chore: update webui to <x>` 로 들어오고, 릴리스 commit 은 브랜치가 가진 bundle 을 그대로 싣는다. WebUI 가 rc 기간을 놓치면 `.0` 은 현재 bundle 로 일정대로 나가고 update 는 다음 patch 릴리스에 담긴다. 그래서 bundle 만 올리기 위해 patch 릴리스가 존재할 수 있고, 이것이 "patch 릴리스는 백포트된 fix 만 기록한다"(3.(c))의 유일한 예외다.

**각 tree 가 자기 bundle 을 소유한다.** fragment pool 과 같다. `main` 은 개발 중인 버전의 bundle 을, 버전 브랜치는 자기 bundle 을 가지고 각자 자기 PR 로 변경한다. 4718개 파일을 두 tree 사이에서 cherry-pick 하는 일은 없다.

rc 기간에 rc bundle 을 고정하는 것은 이미 확립된 관행이다(과거 고정 예: `25.18.0-rc.1`, `25.13.0-rc.2`, `25.12.0-rc.1`). 덕분에 rc2 에서 최종 릴리스 전에 UI 를 검증할 수 있다.

### (e) 릴리스 절차

이것이 확립된 뒤에 누가 무엇을 하는지 정리한다.

| 단계 | 주체 | 동작 |
|---|---|---|
| 분기 1 | 사람 | `cut-release-branch.sh <version>` 실행 → PR `release: <version>.0rc1` 생성 |
| 분기 2 | CI | `check-version-change` 가 release 접두사를 확인. 전체 test suite |
| 분기 3 | 사람 | squash merge |
| 분기 4 | **자동** | merge commit 에 `<version>.0rc1` tag(PAT)를 붙이고 `<version>` 브랜치 생성 |
| 분기 5 | **자동** | tag push → `ci.yml make-final-release` → wheel 과 `supergraph.graphql` 만 담은 GitHub Release(prerelease) |
| rc 기간 | **자동** | `main` 에 merge 된 fix PR → `backport.yml` 이 `<version>` 에 cherry-pick PR 생성. 성공은 auto-merge, 충돌은 draft PR + `pending:backport` |
| rc 기간 | 사람 | 충돌한 draft PR 을 해결. 검증이 더 필요하면 브랜치에서 `release.sh <version>.0rc2` |
| rc 기간 | WebUI | rc1 `supergraph.graphql` asset 을 기준으로 빌드해 bundle 을 배포. 여기에 `chore: update webui to <x>` PR 로 들어온다 |
| 최종 1 | 사람 | 브랜치에서 `release.sh <version>.0` → PR → merge |
| 최종 2 | **자동** | `<version>.0` tag → GitHub Release + PyPI |
| 최종 3 | **자동** | `changelog-sync.yml` 이 `CHANGELOG-<version>.md` 를 복사하는 `main` PR 생성 |
| patch | - | `<version>.1` 이후는 최종과 같은 경로 |

사람이 하는 일은 script 두 개를 실행하고 PR 두 개를 merge 하고 백포트 충돌을 해결하는 일이다. tag 생성, 브랜치 생성, 변경 기록 복사는 자동이다.

rc 릴리스는 alpha 처럼 wheel 과 `supergraph.graphql` 을 담은 GitHub prerelease 로만 나간다. Scies, SBOM, conda pack, PyPI upload 는 최종 릴리스에만 담긴다.

### (f) 작업 범위

| 작업 | 내용 |
|---|---|
| **CI 의 버전 관리** | 새 `cut-release-branch.sh`(분기 PR 절차 전체. `release.sh` 에서 freeze/bump 를 흡수한다), release PR merge 시 `merge_commit_sha` 로 tag 와 브랜치를 생성하는 workflow, `main` 의 `VERSION` 정렬 |
| **registry 기반 백포트 + 분류 skill** | `maintained-versions.yml` 도입, push 된 commit 이 아니라 merge 된 PR(`pull_request_target` + `/backport` comment)에서 `backport.yml` 을 실행, 접두사와 `Backport:` trailer 로 대상 결정, `-X theirs` 제거, 충돌 시 draft PR, `Backported-*` trailer 제거, edge 와 stable installer 채널 선택을 registry 로 이전, `pending:backport` PR 을 나열하고 각각을 처리하는 Claude skill(충돌을 해결하거나, fix 가 그 버전에 적용되지 않는 이유를 적어 닫는다) |
| **WebUI 분리** | `release.sh` 에서 `webui_version` 을 제거해 bundle 을 자기 PR 로 고정, `graphql-inspector` 대상을 `supergraph.graphql` 로 변경, 버전 브랜치 PR 에서 새로 추가된 `NEXT_RELEASE_VERSION` 참조를 거부하는 CI check 추가, 선택적으로 `static/version.json` 이 릴리스 버전보다 뒤처지면 경고 |
| **변경 기록 분리와 script 정리** | 임시 towncrier config 로 버전 브랜치별 파일 생성(상대 `directory`/`template` 경로가 해석되도록 저장소 루트에 작성한다), towncrier skip guard, `extract-release-changelog.py` 의 hardcoding 과 prerelease 처리, 새 `changelog-sync.yml`, `daily-workflows.rst` 변경 |

## 4. 결정 요약

| 결정 | 내용 |
|---|---|
| 분기 시점 | 기능이 끝났을 때 **`main` 의 rc1 릴리스** |
| 분기 동작 | rc1 tag 생성과 버전 브랜치 생성은 **같은 merge commit 에서 하는 한 동작**이고, `merge_commit_sha` 에서 자동화한다. 브랜치는 commit 0개로 시작하고, rc1 은 브랜치에서 다시 tag 하지 않는다 |
| 분기 절차 | **PR 하나**로 수행하고 `cut-release-branch.sh` 가 생성한다. `VERSION`, freeze, NEXT 올리기, 재생성, towncrier, 버전 등록 |
| script 분리 | `cut-release-branch.sh`(`main`, 분기 전용)와 `release.sh`(버전 브랜치, freeze/bump 없음)를 나눈다. 재생성 helper 만 공유한다 |
| `VERSION` | 그 tree 가 **마지막으로 릴리스한** 버전. 릴리스 commit 만 갱신하므로 항상 tag 와 일치하고, 빌드 시 덮어쓸 필요가 없으며, rc 가 PyPI 에 최종 버전을 주장하는 일이 구조적으로 불가능해진다 |
| `NEXT_RELEASE_VERSION` | 분기 PR 에서 고정한 뒤 다음 대상으로 올린다. 브랜치는 자기가 릴리스하지 않는 `<next>.0` 을 그대로 가지므로, 버전 브랜치 PR 은 자기가 배포할 버전을 literal 로 적는다. CI 는 거기서 새로 추가된 참조를 거부한다 |
| 백포트 대상 | milestone 을 제거한다. 제목 접두사가 기본값을 고르고 `Backport:` trailer 가 그것을 대체하며, `maintained-versions.yml` 과 대조한다. label 은 없다 |
| registry 내용 | 살아 있는 line 마다 record 하나: 버전, 장기 지원이면 `lts`, 그리고 `retire_after`. 등급과 지원 기간도 결국 범위 안이다. installer 채널에 등급이 필요하고, 손으로 관리하던 그 값이 이미 낡아 있었다 |
| registry 관리 | `release.sh` 가 line 을 분기하는 `X.Y.0rc1` 에서 등록하고 같은 실행에서 만료 대상을 retire 한다. LTS line 은 `retire_after` 가 지나면, 일반 line 은 더 새로운 line 이 생기면 retire 한다. LTS 여부는 명시적으로 받고 추론하지 않는다 |
| installer 채널 | registry 에서 읽는다. `edge` 는 가장 새로운 유지 버전, `stable` 은 가장 새로운 LTS 이며, 손으로 설정한 repository variable 을 대체한다 |
| 백포트 범위 | **정해진 집합의 모든 대상으로 항상 백포트**하고 미리 거르지 않는다. 적용할 수 없는 cherry-pick 은 draft PR 이 되고 skill 이 해결하거나 이유를 기록해 닫는다 |
| 백포트 실패 | 조용히 덮어쓰지 않고(`-X theirs` 제거) draft PR 로 남긴다 |
| 변경 기록 파일 | **버전 브랜치별**. 릴리스별로 쪼개면 `.0` 파일이 rc 이후 delta 만 가지므로 최종 내용이 `main` 에 이르지 않는다 |
| 변경 기록 내용 | rc 부터 완전한 릴리스 노트이고 최종 릴리스에서 합친다. patch 릴리스는 그 릴리스로 백포트된 fix 만 기록한다 |
| fragment 소유 | 각 tree 가 자기 pool 을 자기 릴리스로 비운다. 뒤로 옮기는 일은 없다 |
| `main` 반영 | 최종 tag 마다 **버전 파일 하나를 복사**한다. cherry-pick 이 아니다 |
| PyPI 의 rc | 배포하지 않는다. rc 는 wheel 과 `supergraph.graphql` 만 담은 GitHub prerelease 다 |
| schema 정책 | rc1 tag 부터 버전 브랜치는 **GraphQL schema 에 추가할 수 있지만 깨뜨릴 수 없다**. rc1 릴리스 asset 은 WebUI 가 의존할 수 있는 schema 의 **하한**이고, 그 버전의 최종 schema 가 아니다 |
| schema 강제 | 기존 `graphql-inspector` job 의 대상을 `schema.graphql` 에서 `supergraph.graphql` 로 변경해 v1 과 v2 를 모두 포괄한다. 26.8 의 breaking change(#13277)는 v2 전용이라 빠져나갔다. merge 차단은 그 job 의 required status check 로 유지한다 |
| WebUI bundle 고정 | 자기 PR 로 고정하고 릴리스 commit 안에서는 하지 않는다. 릴리스는 브랜치가 가진 bundle 을 그대로 담으므로 WebUI 가 `.0` 을 차단하지 않는다. bundle 만 올리기 위해 patch 릴리스가 존재할 수 있다 |
| bundle 소유 | 각 tree 가 fragment pool 처럼 자기 bundle 을 소유한다. tree 사이에서 cherry-pick 하지 않는다 |

## 5. 열린 질문

- **최종 릴리스가 합치기 전까지 rc 릴리스가 자기 릴리스 제목 블록을 두는지**, 아니면 처음부터 최종 블록에 쓰는지. 오늘의 `CHANGELOG.md` 는 전자가 기존 관행임을 보여준다(rc 제목 0개가 남았고 rc tag 는 9개다).
- **WebUI bundle 이 결국 릴리스 아티팩트를 떠날 수 있는지**(별도 bundle wheel 이나 설치 시 내려받기. 둘 다 webserver 의 기존 `static_path` 와 호환된다). 아티팩트가 그것을 담아야 하는 동안은 범위 밖이지만, 결합을 일정으로 피하지 않고 없애는 유일한 변경이다.

## 6. 참고

- `.github/workflows/{backport,ci,check-version-change,timeline-check}.yml`, `.github/actions/{pr-title-prefix,detect-release-pr}`
- `scripts/{release.sh,build-wheels.sh,freeze_release_version.py,bump_next_release_version.py,extract-release-changelog.py,determine-release-type.py}`
- `src/ai/backend/common/meta/meta.py`
- `src/ai/backend/manager/models/alembic/README.md`
- `docs/dev/daily-workflows.rst`: "Making a new release", "Making a new release branch"
- 선례: CPython PEP 101 / `Misc/NEWS.d`(`main` 은 b1 까지, 이후는 브랜치 전용), Kubernetes `CHANGELOG/CHANGELOG-1.xx.md`(버전별 파일)
