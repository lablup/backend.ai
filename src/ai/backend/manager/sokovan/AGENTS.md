# Manager Sokovan 레이어 — 가드레일

> Sokovan은 deployment / route 라이프사이클을 tick 단위로 진행시키는 coordinator 레이어다.
> 동작 모델·근거는 같은 디렉터리 `CONTEXTS.md`(및 하위 `README.md`).

## 핸들러 파일 레이아웃

- **핸들러 하나 = 파일 하나**: `sokovan/**/handlers/` 아래 모든 `*Handler` 클래스는 자체 모듈에 둔다.
- 파일명은 그 핸들러가 다루는 라이프사이클 단계/서브스텝을 따른다
  (예: `deploying_provisioning.py`, `deploying_rolling_back.py`, `warming_up.py`, `terminating.py`).
- `base.py`는 추상 `*Handler` 베이스 클래스 전용. 공용 유틸은 별도 모듈에 — `base.py`에 두지 않는다.
- `__init__.py`에 구현을 두지 않는다(re-export는 root 전역 규칙을 따른다).

## 핸들러 vs coordinator 책임

- 핸들러는 해당 동작의 결과(성공 / 실패 / skip 등)만 판단해 반환한다. retry / timeout / give_up 같은
  이력 기반 판단은 핸들러에 넣지 않는다 — coordinator가 공통으로 처리한다.
- 실패 사유는 `DeploymentExecutionError`에 담아 반환한다.

## 상태 전이

- `status_transitions()`는 coordinator가 분류한 각 결과(`success`, `need_retry`, `expired`, `give_up`)의
  목표 라이프사이클을 선언해야 한다. 목표가 없는 결과는 현재 상태에 머문다(`coordinator._handle_status_transitions`).
