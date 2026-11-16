# Manager Sokovan layer: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다. 상세 구조는 `README.md`(`scheduler/README.md`, `deployment/README.md`)에, 설계는 `proposals/BEP-1030`(상태 전이)과 `BEP-1033/*`(scheduler 구조)에 있다.

## 동작 모델 (tick 기반 coordinator)

coordinator(Schedule, Deployment, Replica)는 주기적으로 tick 하나를 실행하며, 대상 상태의 entity 를 조회해 handler 에 전달한다. 유휴 검사기(`idle_check/`)도 sokovan 에 있고 같은 tick 모델을 따른다.

용어: 새 코드와 문서에서는 "route" 보다 **replica** 를 사용한다. `route` 라는 이름(예: `deployment/route/`)은 같은 개념의 legacy 표기(deprecate)다.

- **handler**: 자기 action 의 결과(성공 / 실패 / skip 등)만 판단해 반환한다.
- **coordinator**: retry/timeout/give_up 같은 history 기반 판단과 상태 전이 적용을 중앙에서 맡는다.

가드레일의 근거:
- 각 handler 를 별도 모듈로 두는 이유: lifecycle 단계가 늘어도 "파일 하나 = 단계 하나"라서 격리되고 추적하기 쉽다.
- `status_transitions()` 를 선언식으로 두는 이유: 결과별 대상 상태가 코드에 보여야 coordinator 가 전이를 일관되게 적용하고 감사 기록을 남길 수 있다.
- 책임을 나누는 이유: history 기반 retry/timeout/give_up 을 handler 마다 중복하지 않고 coordinator 가 중앙에서 처리한다.

## scheduler 를 reconcile/stages 구조로 통합

- scheduler 는 reconcile/stages 구조로 전면 통합한다(자세한 내용은 manager 최상위 `AGENTS.md` 참조).
