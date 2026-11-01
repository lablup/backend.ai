# `Unset` sentinel

## 해결하는 문제

클라이언트가 이 field 를 보내지 않은 경우와 클라이언트가 null 을 보낸 경우를 구분한다.

`UNSET` 은 `pydantic_core.MISSING` 이다. pydantic 은 그것을 가진 field 를 serialization 과 JSON schema 에서 뺀다. 그래서 없는 field 는 wire 에 placeholder 를 남기지 않는다.

이전 방식은 `common/api_handlers.py` 의 `Sentinel` enum 이었다. 없는 상태를 정수 `1` 로 serialization 했고, OpenAPI spec 은 이를 `{"type":"integer","enum":[1]}` 로 공개했다.

## `Unset` 이 `MISSING` 이 아니라 `Sentinel` 을 alias 로 두는 이유

`MISSING` 은 PEP 661 sentinel 이므로 annotation 에 사용하려면 type checker 의 PEP 661 지원이 필요하다.

| 도구 | `str \| None \| MISSING` |
|---|---|
| mypy 1.18.2 (현재) | `error: Variable "pydantic_core.MISSING" is not valid as a type` |
| mypy 2.3.1 (최신 release) | 같은 실패 |
| mypy master (2.4.0+dev) | 통과 |
| pyright 1.1.411 | `enableExperimentalFeatures` 로 통과 |

mypy 는 PEP 661 지원을 merge 했지만(`python/mypy#21647`, 2026-08-07) 아직 release 하지 않았다.

그래서 `Unset` 은 정확한 `MISSING` type 대신 값이 속한 실제 class 인 `typing_extensions.Sentinel` 을 참조한다. `isinstance(MISSING, Sentinel)` 이 성립하므로 annotation 은 필요한 것보다 넓지만 거짓이 되지는 않는다. runtime 값은 `MISSING` 으로 남으므로 serialization 동작은 모두 유지된다.

pyright 는 그 넓힘을 거부한다. `MISSING` 을 자체 singleton type 으로 다루기 때문이다. `pants check` 는 mypy 만 실행하므로 CI 는 영향을 받지 않는다.

## `and_optional` / `and_tri` 앞에 명시적 generic 을 두는 이유

pyright 는 `Field(default=UNSET)` 을 거부한다.

```
error: Type "MISSING" is not assignable to declared type "OptionsReq | Unset | None"
```

그러면 field type 은 `Unknown` 이 되고, `from_unset` 이 `TVal` 을 풀지 못하며, 뒤따르는 lambda parameter 도 `Unknown` 이 된다. lambda 본문 전체가 검사되지 않는다.

| | `options` | lambda parameter `o` |
|---|---|---|
| mypy, 추론 | `OptionalState[OptionsReq]` | `OptionsReq` |
| mypy, 명시 | `OptionalState[OptionsReq]` | `OptionsReq` |
| pyright, 추론 | `OptionalState[Unknown]` | `Unknown` |
| pyright, 명시 | `OptionalState[OptionsReq]` | `OptionsReq` |

명시적 generic 은 추론 대신 선언으로 `TVal` 을 고정해 `Unknown` 을 거치지 않는다. 목표는 CI 가 아니라 편집기의 completion 과 검사다.

`Unset` 이 `MISSING` 이 되면 이 규칙은 사라진다.

## `TriState` 에 중첩 접근 메서드가 없는 이유

중첩 request model 은 wire 쪽 묶음이고 뒤에 대응하는 column 이 없다. 비울 것이 없으므로 null 인 parent 는 "이 묶음을 그대로 둔다"는 의미다.

parent 를 `TriState` 로 읽으면 그 null 이 모든 child field 의 NULLIFY 로 번진다. 그러면 nullable 이 아닌 child column 은 제약을 위반하고, nullable 인 column 은 클라이언트가 요청하지 않았는데도 삭제된다.

그래서 중첩 접근은 `OptionalState` 에만 있다. child 의 nullability 는 `and_optional` / `and_tri` 가 정하고, 없는 parent 는 항상 nop 이다.

nullable column 하나를 전체로 차지하는 중첩 model 은 분해하지 않는다. 그 형태는 `TriState.from_unset(...).map(...)` 이다. `api/adapters/deployment_revision_preset/adapter.py` 의 `_convert_model_definition_state` 를 참조한다.

## `isinstance` 를 사용하는 이유

mypy 는 identity 비교를 `None`, enum member, `Literal` 에 대해서만 좁힌다. `value is UNSET` 은 좁히지 않으므로 `from_unset` 본문의 `cls.update(value)` 는 `TVal | Sentinel` 을 받는다.

## mypy 가 PEP 661 을 배포한 뒤

변경되는 곳은 두 곳이다. DTO field 78개와 adapter 는 그대로다.

| 위치 | 변경 |
|---|---|
| `unset.py` | `Unset: TypeAlias = Sentinel` → `TypeAlias = MISSING` |
| `manager/types.py` 의 `from_unset` 본문 두 곳 | `isinstance(value, Unset)` → `value is UNSET` |

`Unset` 은 단순 assignment 가 아니라 `TypeAlias` 로 선언해야 한다. PEP 661 을 지원해도 mypy 는 type 위치의 alias 변수에 `Variable ... is not valid as a type` 을 보고한다.

## 관련 위치

`TriState` / `OptionalState` 는 `manager/types.py` 에 있다. `from_graphql` 은 154개 호출 지점에서 graphql 과 strawberry 에 의존하므로 이 패키지로 옮기지 않았다.
