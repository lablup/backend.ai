# Manager 컴포넌트 — 가드레일

> 컴포넌트 개요·아키텍처는 `src/ai/backend/manager/README.md`.
> 구현 패턴은 루트 `AGENTS.md`가 참조하는 스킬들을 쓴다.

## 레이어 순서 (위 → 아래)

```
api/ → services/ → repositories/ → models/
         ↑ data/ 와 dto/ 는 모든 레이어를 지원
```

## 하위 패키지 (수정 전 해당 디렉터리의 `AGENTS.md`를 읽는다)

- `api/` — HTTP/GraphQL 핸들러
- `services/` — 도메인 검증·비즈니스 로직
- `repositories/` — DB 접근
- `models/` — ORM 스키마
- `data/` — DTO로 변환되는 불변 값 객체
- `dto/` — manager 전용 요청/응답 DTO
- `views/` — 내부 전용 값 객체
- `sokovan/` — 코디네이터·스케줄링

## 레이어 간 규칙

- import는 레이어 순서를 따른다 — 하위 레이어는 상위 레이어를 import하지 않는다.
  (`models/`는 `services/`를, `repositories/`는 `api/`를 import 금지.)
- `data/` 타입은 위로 자유롭게 흐른다. ORM `Row` 타입은 `repositories/` 위로 넘어가면 안 된다.

## 진입점

- `server.py` — HTTP 서버 부트스트랩. 여기 변경은 기동·DI 와이어링에 영향.
- `dependencies/` — 의존성 조립기. 새 의존성은 `server.py`가 아니라 여기 추가.
- `event_dispatcher/` — Manager 측 이벤트 핸들러. 새 이벤트 구독은 여기.

## 에러

- `manager/exceptions.py`와 `manager/errors/`가 둘 다 있으나 `errors/`가 현재 표준.
- 새 도메인 예외는 `manager/errors/{domain}.py`에 — `manager/exceptions.py`에 두지 않는다.

## 스케줄러

- 스케줄링 로직은 `manager/sokovan/scheduler/`에 둔다 — API 핸들러나 service 메서드 안에서
  스케줄링 결정을 하지 않는다.
- **향후 방향:** scheduler를 sokovan의 reconcile·stages 구조로 전체 통합할 예정.
