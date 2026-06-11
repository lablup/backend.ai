# Manager Data 레이어 — 가드레일

> 순수 도메인 타입만 — 프레임워크 의존성 금지.

## 목적

ORM Row와 Service/API 레이어 사이에 놓이는 불변 값 객체. **외부로 전달할 때 DTO로 변환되는 값**이다
(전달 자체는 DTO가 하고, 그 DTO는 이 `data` 값을 토대로 구성한다). DTO로 변환하지 않고 내부에서만
쓰는 값은 `views/`에 둔다 (`manager/views/AGENTS.md`).

이 패키지에는 SQLAlchemy, Pydantic, aiohttp import가 허용되지 않는다.

## 디렉터리 구조 (도메인별)

도메인마다: `data/{domain}/__init__.py`(re-export) + `types.py`(frozen dataclass).

## 타입 규칙

- 모든 data 클래스는 `@dataclass(frozen=True)`여야 한다.
- 허용 import: Python stdlib과 `ai.backend.common.types` — 그 외 금지.
- `manager/models/`, `manager/repositories/`, `manager/services/`, 외부 프레임워크(`pydantic`,
  `sqlalchemy`, `aiohttp`)에서 import 금지.

## 레거시 구분

- v2 / GraphQL 경로가 아닌 레거시 지원용 타입은 이름에 `Legacy`를 붙일 것을 권장한다 —
  가능하면 레거시 타입과 v2 타입을 구분할 수 있어야 한다.

## 여기 속하지 않는 것

- 비즈니스 로직 메서드(순수 데이터 컨테이너만).
- Pydantic 모델 — 요청/응답 타입은 `manager/dto/`나 `common/dto/`를 쓴다.
- 가변 상태나 복잡성을 숨기는 default-factory 필드.
