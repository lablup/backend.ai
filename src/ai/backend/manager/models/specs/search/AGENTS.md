# 검색 필드 선언 — Guardrails

> 배경과 결정 이유는 같은 디렉터리의 `KNOWLEDGE.md`를 본다.

엔티티 검색이 필터하고 정렬할 수 있는 것을 선언한다. 선언은 SQL 연산만 가지며, 필터 DTO를 해석하는 것은 어댑터(`repositories/base/filter_adapter.py`)의 `apply_*_filter`다.

## 엔티티 선언의 모양

- 엔티티마다 `models/{entity}/searchable_fields.py`에 입구 클래스 `{Entity}SearchableFields` 하나를 둔다.
- 입구는 세 속성을 가진다. 개별 클래스는 private(`_{Entity}OwnFields` 등)으로 두고, 바깥에서는 입구 속성으로만 접근한다.

| 속성 | 담는 것 | 권한 |
|---|---|---|
| `own` | 자기 컬럼. `SearchableField(column, filter, order)`. `RowDataConverter`를 구현해 row에서 data를 만듦 | 이 엔티티의 field cap |
| `nested` | 소유한 다른 테이블 행(labels, mount policy 등, dangling field 포함). 읽기 권한이 이 엔티티 권한인 것만. `NestedSearchableField(상대 입구.own, correlation)` | 이 엔티티의 field cap (`labels.key`) |
| `linked` | 다른 엔티티와의 연결(`MembershipConditions` 등) | 스코프, 상대 엔티티 권한 |

- data 필드마다 같은 이름의 `SearchableField`를 두고, `to_data`는 모든 값을 `self.<이름>.read(row)`로 읽는다. data 생성자가 모든 필드를 요구하므로 선언을 빠뜨리면 mypy가 실패한다.
- Row 클래스에 `to_data` 같은 메서드를 두지 않는다. 호출부는 `{Entity}SearchableFields.own.to_data(row)`를 쓴다.
- 필터와 정렬 칸은 모두 채운다. `None`은 할 수 없는 경우에만 쓴다: JSON/JSONB, 배열, `SecretColumn`, 파생 필드. `DecimalType`(VARCHAR)은 숫자로 캐스트한 식으로 정렬한다.
- API에 무엇을 여는지는 필터 DTO와 정렬 필드 enum이 정한다. 선언은 할 수 있는 것만 적는다.
- 속성 이름은 필터 DTO 필드명, data 필드명, field cap 경로와 같게 둔다.
- 선언은 클래스 속성으로 둔다. 모듈 전역 인스턴스를 만들지 않는다.

## 조건과 정렬

- 값 타입별 조건 클래스(`conditions/`)는 컬럼 하나와 연산 메서드만 가진다. 필터 DTO를 import하지 않는다.
- 연산은 `None`을 받지 않는다. 설정되지 않은 필터 필드를 건너뛰는 것은 `apply_*_filter`의 일이다.
- 공통 구현으로 안 되는 필드는 해당 연산 하나만 바꾼 하위 클래스를 엔티티 모듈에 둔다.
- 정렬 필드 enum 변환은 `match`로 쓰고 `case _: assert_never(...)`로 끝낸다.

## 다른 테이블 행

- 다른 테이블 필드는 펼치지 않고 `nested`에 중첩으로 선언한다. 조건을 모아 EXISTS 하나로 묶어야 같은 행에 걸린다.
- to-many는 `ToManyCorrelation`(some / every / none), to-one은 `ToOneCorrelation`(has, 정렬)을 쓴다.
- `Correlation`이 만든 조건과 정렬은 `correlate_row`를 FROM에 가진 쿼리 안에서만 쓴다.
- `Relation`이라는 이름을 쓰지 않는다. 권한 쪽(`specs/relation.py`, BEP-1075)의 연결 행과 겹친다.

## 다른 엔티티

- 다른 엔티티의 필드로 거르는 중첩 필터를 두지 않는다. 다른 엔티티와의 관계는 스코프로 표현한다.
- 다른 엔티티는 자기 컬럼에 저장된 식별자(`creator_id`, `domain_name` 등)로만 거른다. 이름이나 상태로 거르려면 상대 엔티티를 먼저 조회해 id를 구한다.
- 자기 권한 타입을 가진 부속 행(entity share 등)은 `nested`에 두지 않는다. 그 엔티티의 검색에서 스코프로 다룬다.

## 엔티티 사이의 사용 관계

- session → vfolder처럼 소유가 아닌 사용 관계는 소유 그래프에 올리지 않는다. 사용하는 쪽 테이블 컬럼으로 판정한다.
- FK 컬럼만 사용 관계로 본다. JSON 값 안의 id는 사용 관계가 아니다.
- `linked`에 `UsageConditions[{사용 엔티티}ID]`로 선언하고, 속성 이름은 사용 엔티티의 복수형으로 둔다(`deployments`, `model_cards`). `used_by(id)`는 `UsedBy`를 반환한다.
- scope 검색은 `UsedBy`를 `ScopedSearcher`로 넘긴다. 호출자는 각 사용 엔티티를 읽을 수 있어야 하며, 못 읽으면 검색 전체를 거부한다. 결과는 scope가 허용한 행으로 한정되고, 사용 관계는 권한을 주지 않는다.
- SUPERADMIN 게이트를 거치는 global 검색은 검사할 것이 없으므로 `UsedBy.condition`을 조건으로 바로 건다.
