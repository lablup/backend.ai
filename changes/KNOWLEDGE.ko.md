# changes/: 배경

> 규칙은 `changes/README.md` 에 있다(파일 이름 규칙, 문체).

## 이 디렉터리가 있는 이유

PR 제목과 변경 기록 항목(`changes/<...>.<type>.md`)은 서로 다른 곳에 있지만 같은 분류를 공유한다. 이 문서는 그 분류와, `fix:` 가 자동 백포트를 유발해서 생기는 예외(같은 릴리스의 수정)를 담는다.

## 카테고리, PR 제목 접두사, changelog 유형의 대응

| 카테고리 | PR 제목 접두사 | changelog 유형 | 비고 |
|---|---|---|---|
| 새 기능 | `feat` | `feature` | |
| 버그 수정, 이미 지원 중인 릴리스 브랜치에 있음 | `fix` | `fix` | 지원 중인 모든 버전으로 자동 백포트한다 |
| 버그 수정, 같은 미출시 주기에 들어온 코드 | `chore` | `misc` | 출시된 적이 없어 백포트 대상이 아니다 |
| 성능, 리팩터링 | `refactor`/`perf` | `enhance` | |
| 호환되지 않는 API 변경 | 기반 commit 유형 유지 (`feat`/`refactor`/...) | `breaking` | 전용 접두사 없음, 유형은 그대로 두고 changelog 만 breaking 으로 분류한다 |
| 테스트만 있는 변경 | `test` | `test` | |
| 문서 | `doc` | `doc` | |
| 의존성 변경 | `deps` | `deps` | |
| 기존 기능 지원 중단 | 기반 commit 유형 유지 (`chore`/`feat`/...) | `deprecation` | 전용 접두사 없음 |

## 같은 릴리스의 수정이 `fix` 가 아닌 이유

- `fix:` PR 은 `.github/maintained-versions.yml` 에 등재된 지원 중인 모든 버전으로 자동 백포트한다.
- 이 동작은 버그가 이미 지원 중인 브랜치에 있을 때만 타당하다.
- 버그가 있는 코드가 `main` 에만 있다면, 같은 미출시 주기에 앞서 들어온 코드라면, `fix` 로 표시할 때 출시된 적 없는 코드를 백포트하게 된다.
- 그래서 PR 제목은 `chore` 를, 변경 기록 항목은 `misc` 를 사용한다.

## 변경 기록 항목을 PR 번호 없이 이름 지을 수 있는 이유

- `<PR-number>.<type>.md` 이름은 PR 을 연 뒤에만 넣을 수 있고, 그 두 번째 push 로 PR 의 CI 를 처음부터 다시 실행한다.
- `<YYYYMMDD>-<HHMMSS>-<6 chars>.<type>.md` 이름은 코드와 같은 첫 push 에 넣는다. 이슈 키 유무와 상관없이 이 이름을 권장한다.
- PR 번호는 릴리스 때 git 이력에서 붙인다. 파일을 추가한 first-parent 커밋 제목에 squash merge 나 백포트가 남긴 `(#N)` 이 있다.
- 이름을 변경하며 front matter 를 떼므로 towncrier 는 지금처럼 `<PR-number>.<type>.md` 만 읽는다.

## 에픽 파일을 두는 이유

- 에픽 단위 작업을 릴리스 노트에서 묶어 보이기 위해 에픽과 하위 이슈의 관계를 fragment 를 쓸 때 남긴다(`epic`).
- 에픽 제목과 요약은 `changes/epics/` 에 한 번만 쓰고 PR 에서 리뷰한다. 릴리스 때 트래커를 조회하지 않는다.
- 에픽은 여러 릴리스에 걸치므로 에픽 파일은 릴리스 때 소비하지 않는다.
- `changes/epics` 는 `pyproject.toml` 의 towncrier `ignore` 에 있다. towncrier 는 점이 없는 이름을 잘못된 fragment 이름으로 보고 멈춘다.
- towncrier 를 쓰지 않게 되면 번호 방식과 towncrier 설정을 함께 정리한다.
