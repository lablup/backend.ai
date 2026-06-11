# 테스트 가이드라인 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`. 워크플로·패턴·코드 예시는 `/tdd-guide` 스킬.

## 전략 구분 근거 (실 DB vs 모킹)

- Repository/Model은 실제 동작이 중요한 통합 지점이라 실 DB로 검증한다.
- 그 외 레이어는 로직 검증이 핵심이라, 격리가 속도와 명료함을 높인다.

## "구현이 아니라 동작" — 하지 말 것 예시

- 내부 호출 배선 단언: `savepoint()`가 `session.begin_nested()`를 부르는지, `write_ops()`가 특정 세션 메서드를
  여는지, 어떤 위임 함수가 불렸는지 스파이 — 무해한 리팩터에 깨지고 호출자가 실제로 의존하지 않는 것을 검증한다.
- 하위 레이어가 자체 테스트로 이미 검증한 위임 로직 재단언(이미 테스트된 `execute_*`로 포워딩하는 얇은 래퍼 등).

## 테스트 실행

```bash
pants test tests/manager::                                   # 디렉터리 전체
pants test tests/manager/repositories/test_fair_share.py     # 특정 파일
```

변경 영향 범위는 CI에 맡기고, 로컬에선 직접 관련된 테스트를 타게팅한다
(광범위한 `--changed-dependents=transitive` 스윕은 지양).
