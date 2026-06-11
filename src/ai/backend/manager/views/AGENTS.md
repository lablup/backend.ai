# Manager Views 레이어 — 가드레일

> 내부에서만 쓰는 값 객체(read-projection 등)를 두는 곳.

## 목적

전체적으로 내부에서만 쓰는 값을 두는 곳. `data/`와 달리 DTO로 변환해 외부로 전달하지 않는다
(`manager/data/AGENTS.md`). 예를 들어 ORM row에서 조립해 coordinator / 스케줄링 레이어로 넘기는
read-projection이 여기 속한다.

## 타입 규칙

- 평범한 `@dataclass`(프레임워크 의존성 없음 — SQLAlchemy, Pydantic, aiohttp 금지).
- `data/`와 `common/identifier/`에서 enum / 식별자를 import할 수 있다(views는 data 위에 위치).
- 비즈니스 로직 메서드 금지 — 순수 컨테이너.
