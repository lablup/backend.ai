---
name: search-field-declarations
type: design-rationale
description: why search filters and orders are declared per field instead of per-entity condition functions, why the declaration builds the data type from a row, why condition classes do not know filter DTOs, why operations reject None, the own / nested / linked split and its permission axes, nested versus flattened fields of other tables, the Correlation naming, why usage relations between entities stay out of the ownership graph, what field caps need from the declarations, how other services bound relational filters
scope: src/ai/backend/manager/models/specs/search
keywords: [SearchableField, NestedSearchableField, RowDataConverter, ToManyCorrelation, ToOneCorrelation, StringConditions, EnumConditions, MembershipConditions, ConditionOrder, apply_string_filter, apply_to_many_filter]
sources:
  - src/ai/backend/manager/models/specs/search
  - src/ai/backend/manager/models/specs/conditions
  - src/ai/backend/manager/models/specs/orders
  - src/ai/backend/manager/repositories/base/filter_adapter.py
  - src/ai/backend/manager/models/vfolder/searchable_fields.py
  - src/ai/backend/manager/models/entity_label/searchable_fields.py
generated:
  by: claude-code/opus-5
  at: 2026-09-19
status: draft
---

# 검색 필드 선언 — Knowledge

> 규칙은 같은 디렉터리의 `AGENTS.md`에 있다.

엔티티마다 필드 × 연산 수만큼 손으로 쓰던 조건 함수와 정렬 메서드를, 필드 하나당 선언 하나로 바꾸기 위한 패키지다. 필터, 정렬, 권한(field cap)이 같은 필드 목록을 보게 하는 것이 목적이다.

## 필드 단위로 선언해야 누락을 검사할 수 있다

- 함수 방식에서는 "필드"가 함수 이름 규칙 안에만 있어서, 연산이나 정렬이 빠져도 드러나지 않았다.
- 선언은 필터 칸과 정렬 칸을 함께 가지므로, 필터나 정렬이 가능한지가 선언에서 바로 보인다.
- 정렬은 `match` + `assert_never`로 mypy가 검사하고, 필터 DTO와 선언의 짝은 스윕 테스트로 검사한다.

## 선언이 row에서 data를 만들어야 누락이 타입으로 막힌다

- 테스트로 선언과 data를 대조하면, 테스트가 빠지거나 대상 등록이 빠질 때 누락을 막지 못한다.
- `RowDataConverter.to_data`가 data 생성자를 직접 부르고 모든 값을 선언의 `read(row)`로 읽으면, data에 필드를 추가하는 순간 선언이 없으면 mypy가 실패한다.
- `read`는 컬럼의 값 타입을 돌려주므로 선언과 data 필드의 타입 짝도 mypy가 본다.
- 인자를 선언 대신 `row.x`로 직접 읽는 우회는 타입으로 막을 수 없고, 리뷰로 막는다.

## 정렬은 막을 이유가 없으면 모두 선언한다

| 컬럼 종류 | 정렬 | 이유 |
|---|---|---|
| JSON/JSONB, 배열 | 불가 | 문서 구조, 순서가 의미 없음 |
| `SecretColumn` | 불가 | 암호문 비교는 의미가 없고 값 추정의 단서가 됨 |
| `DecimalType` | 캐스트 필요 | VARCHAR 저장이라 `"10" < "9"` |
| enum | 가능 | 알파벳 순. 의미 순서는 아님 |
| 그 밖의 스칼라 | 가능 | |

- 노출 여부는 정렬 필드 enum이 정한다. 비용(인덱스 없는 정렬)은 enum에 필드를 추가할 때 검토한다.

## 조건 클래스는 필터 DTO를 모른다

| 계층 | 가진 것 |
|---|---|
| models (`conditions/`, `orders/`, `search/`) | 컬럼과 SQL 연산 |
| 어댑터 기반 (`BaseFilterAdapter.apply_*_filter`) | DTO 필드를 연산 호출로 바꾸는 분기 |
| common DTO | 필드만. `EnumFilter[E]`, `ToManyFilter[F]` 같은 generic 기반도 로직이 없음 |

- models가 API DTO를 import하지 않도록 분기를 어댑터에 둔다.
- 분기는 이전에 DTO, 어댑터, GQL 타입에 세 벌 있었고, 어댑터 한 벌로 모은다.

## 연산이 None을 받지 않는다

- `None`을 받게 하면 값을 확실히 가진 호출(guard, handler)도 반환 타입이 `QueryCondition | None`이 되어, 실행되지 않는 분기가 생긴다.
- `@overload`로 좁히는 방법은 연산마다 선언이 늘어서 쓰지 않는다.
- 설정되지 않은 필드를 건너뛰는 일은 `apply_*_filter` 한 곳에서 한다.

## own / nested / linked는 권한이 적용되는 방식으로 나눈다

| 부분 | 기준 | 권한 |
|---|---|---|
| own | 자기 테이블 컬럼 | 이 엔티티의 field cap |
| nested | 다른 테이블에 있지만 이 엔티티가 소유한 행 | 이 엔티티의 field cap (경로 `labels.key`) |
| linked | 다른 엔티티와의 연결 | 스코프, 상대 엔티티 권한 |

- 테이블이 아니라 소유 여부로 나눈다. labels는 다른 테이블이지만 vfolder의 데이터다.
- 입구 하나로 모으면 스윕 테스트와 권한 검사가 한 곳에서 시작한다. 개별 클래스는 이름으로 참조할 일이 없어 private이다.

## 다른 테이블 필드는 펼치지 않고 중첩한다

| | 펼치기 (`label_key`, `label_value`) | 중첩 (`labels.key`) |
|---|---|---|
| 조건의 묶음 | 필드마다 EXISTS가 따로 걸려, key와 value가 다른 라벨에 맞아도 통과 | 조건을 모아 EXISTS 하나. 같은 라벨에 맞아야 함 |
| some / every / none | 표현 못 함 | `ToManyCorrelation`이 제공 |
| 경로 | 이름을 새로 지어야 함 | field cap 경로, 조회 경로와 같은 모양 |

- every는 `NOT EXISTS(NOT P)`라 자식이 없으면 참이다 (BEP-1060).
- dangling field(라벨)는 FK 대신 `(entity_type, entity_id)`로 잇는다는 점만 다르고, 같은 to-many다.

## 다른 엔티티로의 중첩 필터는 권한 확인이 없어서 두지 않는다

- 스코프는 검증기가 호출자의 권한을 미리 확인하지만, 중첩 필터는 EXISTS 안에서 상대 행의 값을 행마다 평가할 뿐 호출자가 그 행을 읽을 수 있는지는 보지 않는다.
- 그래서 필터 결과로 읽을 수 없는 행의 값(예: 다른 사용자의 이메일)을 추정할 수 있다.
- 필요한 경우(관계 엔티티의 상태, 표시 값 검색, 관계 속성 정렬)는 두 단계 조회나 자기 컬럼에 복제된 식별자로 대신한다.
- 열어야 할 때는 "호출자가 읽을 수 있는 행" 조건을 EXISTS 안에 함께 넣는 공통 부품이 먼저 필요하다.
- entity share처럼 자기 권한 타입을 가진 부속 행도 같은 이유로 `nested`에 두지 않는다.

## Relation 대신 Correlation이라 부른다

- `Relation`은 BEP-1075에서 "두 엔티티가 함께 소유하는 연결 행"을 뜻한다.
- 이 패키지의 타입은 바깥 행과 연결된 다른 테이블 행을 상관 서브쿼리로 찾을 뿐이라, SQL 용어를 그대로 쓴다.
- `.correlate()`는 바깥 SELECT에 그 테이블이 있을 때만 서브쿼리 FROM에서 뺀다. 바깥 쿼리 없이 쓰면 교차 조인이 된다.

## 사용 관계는 그래프에 올리지 않는다

- govern은 "스코프의 역할이 대상이 소유한 것 전부에 닿는다"는 뜻이라, session을 다스리는 project 역할이 마운트된 vfolder까지 닿게 된다.
- own + cap(공유)은 엔티티 단위 권한에서는 번지지 않지만, 스코프 검색의 도달 판정은 cap을 보지 않아 목록이 새어 나간다.
- 그래서 사용 관계는 좁히기만 한다. `결과 = 사용 관계(테이블 컬럼) AND 결과 쪽 읽기 권한 AND 사용하는 쪽 읽기 권한`.
- 이렇게 하면 권한 규칙을 새로 만들지 않고, 사용 관계의 기준 데이터도 기존 컬럼 하나로 남는다.

## field cap은 선언에서 세 가지를 요구한다

| 요구 | 이유 |
|---|---|
| 선언 이름 = 필터 DTO 필드명 = data 필드명 = cap 경로 | 요청 경로를 변환 없이 cap 경로로 쓴다 |
| 행마다 가리기 | 공유가 필드 경로 단위라 같은 필드도 행마다 cap이 다르다. 필터는 `cap AND 조건`, 정렬은 `CASE WHEN cap THEN 컬럼 END` |
| 정렬도 검사 | 응답에 싣지 않아도 정렬과 반복 필터로 값이 샌다 |

## 다른 서비스는 관계 필터를 이렇게 연다

| 서비스 | 여는 것 | 깊이 |
|---|---|---|
| Stripe, GitHub, Jira | FK id, 이름 같은 식별자 | 0~1 |
| Kubernetes | 자기 라벨 | 0 |
| Linear, Prisma, Hasura | 관계 엔티티 필터 전체 | 제한 없음 |
| Hasura depth limit | 선택 집합만 셈. 필터 조건은 세지 않음 | 해당 없음 |

- 공개 API일수록 식별자와 소유 부속까지만 연다.
- 이 패키지는 소유한 것은 모두 열고 field cap으로 줄이며, 다른 엔티티와의 관계는 스코프로 표현하는 쪽을 택했다.
