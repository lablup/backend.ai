# Manager Models 레이어 — 가드레일

> 이 레이어는 ORM 스키마만 정의한다. 쿼리 패턴은 `/repository-guide`, 데이터 타입 규약은
> `manager/data/AGENTS.md` 참고.

## 디렉터리 구조 (도메인별)

모든 도메인은 `models/{domain}/__init__.py`(re-export만) + `row.py`(ORM 클래스)를 따른다.
단일 파일 단축형(`models/simple.py`)은 legacy — 새로 추가하지 않는다.

## Row 클래스 규칙

- `Base`(`manager/models/base.py` 정의)를 상속한다.
- 모든 Row 클래스에 `__tablename__`이 필요하다.
- 엔티티 간 관계: 관련 Row import는 `TYPE_CHECKING` 블록 안에만 둔다.

## Row 클래스에 로직 금지

- Row 클래스에 쿼리 빌더 메서드를 추가하지 않는다 — `repositories/db_source/` 소관.
- 비즈니스 로직 메서드를 추가하지 않는다 — `services/` 소관.
- `session/row.py`에 legacy 쿼리 메서드가 있으나 그 패턴을 따르지 않는다.

## 커스텀 컬럼 타입

- 가능하면 `models/base.py`의 기존 `TypeDecorator` 래퍼를 재사용한다.
- 새 `TypeDecorator`는 `models/base.py`에만 추가한다 — 개별 row 파일에 두지 않는다.

## `__init__.py` 규칙

- `row.py`에 선언된 Row 클래스만 re-export한다 — 그 외 금지.
