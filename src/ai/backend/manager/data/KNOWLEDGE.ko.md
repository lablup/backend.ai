# Manager data: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 경계 기준

데이터를 다루는 패키지 축은 넷이다: `data/`, `dto/`, `schema/`, `views/`. common 과 컴포넌트마다 둘 수 있지만 DB 에 접근하는 것은 manager 뿐이므로 `views/` 와 DB 와 결합한 schema 선언은 manager 에만 둔다. 값이 어디로 가는지에 따라 판단한다.

| 값의 성격 | 위치 |
|---|---|
| API 응답의 일부로 프로세스 밖으로 나간다 | `data/`: adapter 에서 DTO 로 변환한다 |
| 통신 형식 자체다(검증된 요청과 응답) | `dto/`(manager 전용) 또는 `common/dto/`(공유) |
| 구조 선언이다(검증 가능한 schema 타입) | `schema/`, 예: `common/schema/` |
| 결정을 위한 내부 조회 projection 이다(scheduler, coordinator) | `views/`, manager 전용 |

`data/` 는 repository 가 ORM row 대신 반환하는 값이다. 위 계층으로 자유롭게 흐르고, row 는 그렇지 않다.

## 자기 도메인의 row 만 담으면 조회가 요청한 범위에 머문다

- 다른 테이블의 값을 담으면 그 값을 산출하는 모든 조회가 그 row 까지 접근한다. 목록 조회에서는 이 비용이 row 수만큼 곱해진다.
- async session 에서 그런 조회는 `MissingGreenlet` 을 일으킨다. eager load 는 에러를 피할 뿐 비용은 줄이지 못한다.
- eager load 가 포함하는 도메인은 단일 엔티티 read/write spec(`models/specs/`)의 범위를 벗어난다. 그 spec 은 `sa.select(Row)` 하나로 표현되는 읽기를 전제한다.

## Undefined sentinel 은 부분 수정에서 "제공되지 않음"을 나타내는 표시다

- `data/common/sentinel.py` 가 `Undefined`/`undefined` singleton 을 정의하고 `TriState` 와 짝을 이룬다.
- 의미: 없음 = 유지, sentinel = 초기화, 값 = 설정.
- DTO 수준 SENTINEL pattern(`common/dto/manager/v2/KNOWLEDGE.md`)의 manager 쪽 대응이다.

## 정한 규칙과 현재 코드는 어긋난다

- 순수성 규칙(frozen dataclass, stdlib 와 `common.types` 에서만 import)은 목표 상태이고 현재 상태가 아니다.
- 알려진 차이: 여러 session 과 deployment 모듈의 pydantic, SQLAlchemy column 을 아는 `data/common/types.py` 의 filter 타입, frozen 보다 많은 가변 creator 와 modifier dataclass.
- 규칙은 새 코드의 방향으로 다룬다. 기존 위반을 선례로 인용하지 않고, 전용 정리 작업 밖에서 일괄 수정하지 않는다.
