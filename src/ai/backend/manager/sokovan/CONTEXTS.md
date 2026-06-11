# Manager Sokovan 레이어 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`. 상세 아키텍처는 `README.md`(및 `scheduler/README.md`,
> `deployment/README.md`), 설계는 `proposals/BEP-1030`(상태 전이)·`BEP-1033/*`.

## 동작 모델 (tick 단위 coordinator)

coordinator(Schedule / Deployment / Route)는 주기적으로 한 tick을 돌며, 대상 상태의 엔티티를 조회해
핸들러에 넘긴다.

- **핸들러**: 해당 동작의 결과(성공 / 실패 / skip 등)만 판단해 반환한다.
- **coordinator**: retry / timeout / give_up 같은 이력 기반 판단과 상태 전이 적용을 공통으로 가져간다.

가드레일의 근거:
- 핸들러가 자체 모듈인 이유 — 라이프사이클 단계가 늘어도 "한 파일 = 한 단계"로 격리돼 추적이 쉽다.
- `status_transitions()`를 선언적으로 두는 이유 — 결과별 목표 상태가 코드에 드러나야 coordinator가
  일관되게 전이를 적용하고 감사 이력을 남길 수 있다.
- 책임을 나눈 이유 — 이력 기반 retry/timeout/give_up을 핸들러마다 중복하지 않고 coordinator가 공통 처리한다.

## 향후 방향

- scheduler를 reconcile·stages 구조로 전체 통합 예정(상세는 manager 최상위 `AGENTS.md`).
