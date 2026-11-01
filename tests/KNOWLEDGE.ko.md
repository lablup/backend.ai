# 테스트 지침: 배경

> 규칙은 이 디렉터리의 `AGENTS.md` 에 있다. workflow, pattern, code example 은 `/test-guide` skill 에 있다.

## 전략 구분의 근거: real DB 와 mock

- repository 와 model 은 실제 동작이 중요한 integration point 이므로 real DB 로 검증한다.
- 다른 계층은 logic 검증이 핵심이므로 격리가 속도와 명확성을 높인다.

## "behavior, not implementation": 하지 말아야 할 예

- 내부 호출 경로를 단언하는 검사다. `savepoint()` 가 `session.begin_nested()` 를 호출하는지, `write_ops()` 가 특정 session method 를 여는지, 어느 delegation function 이 호출되는지를 감시한다. 이런 검사는 무해한 refactor 에서 깨지고 caller 가 실제로 의존하지 않는 것을 검증한다.
- 하위 계층의 test 가 이미 검증한 delegation logic 을 다시 단언하는 검사다. 예를 들어 이미 검증된 `execute_*` 로 전달하는 얇은 wrapper 가 그렇다.

## 테스트 실행

```bash
pants test tests/manager::                                   # whole directory
pants test tests/manager/repositories/test_fair_share.py     # specific file
```

변경 영향 범위는 CI 에 맡기고, local 에서는 직접 관련된 test 만 대상으로 한다. 넓은 범위의 `--changed-dependents=transitive` 실행은 피한다.
