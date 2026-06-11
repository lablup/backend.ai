# Manager Services 레이어 — 가드레일

> 구현 패턴은 `/service-guide` 스킬 참고.

## 디렉터리 구조 (도메인별)

도메인마다: `services/{domain}/types.py`, `service.py`, `processors.py`,
그리고 `actions/{base,{operation}}.py` — `actions/` 아래 오퍼레이션당 한 파일.

## Action 규칙

- Action과 ActionResult는 반드시 `@dataclass(frozen=True)`.
- action 파일 하나에 `Action` + `ActionResult` 정확히 한 쌍.
- 모든 구체 Action은 `entity_id()`와 `operation_type()`를 오버라이드해야 한다.

## Service 메서드 규칙

- 한 service 메서드에서 여러 repository를 호출하는 것은 비권장 — tx가 보장되지 않으면 수정한다.
  단, 다른 레이어와 엮인 경우 service에서 다른 동작을 수행한 뒤 repository를 호출하는 것은 허용한다.
- service 메서드는 DB 세션/트랜잭션을 생성하면 안 된다 — repository에 위임한다.
- 각 메서드는 Action을 받아 ActionResult를 반환한다 — 그 외 반환 타입 금지.

## Processor 규칙

- 모든 service 메서드는 `ActionProcessor`로 감싼다. raw service 메서드를 핸들러에 노출 금지.
- `AbstractProcessorPackage`를 상속하고 `supported_actions()`를 오버라이드해야 한다.

## 여기 속하는 것

- 도메인 검증과 비즈니스 규칙.
- 여러 repository에 걸친 오케스트레이션(예외적이며, 정당화가 필요).

## 여기 속하지 않는 것

- SQL 쿼리나 ORM 연산.
- HTTP 요청/응답 처리.
- 직접 DB 세션 생성(`begin_session()` / `begin_readonly_session()`).
