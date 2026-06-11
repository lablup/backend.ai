# Common 패키지 — 가드레일

> 모든 컴포넌트(manager, agent, storage, client SDK)가 이 패키지에 의존한다.
> 여기 변경은 시스템 전체에 영향을 준다 — 무엇이든 수정 전 모든 호출자를 확인한다.

## 여기 속하는 것

- 둘 이상의 컴포넌트가 공유하는 추상화·유틸리티.
- 기본 예외 클래스, 이벤트 타입, DTO 베이스 클래스, 공용 타입 정의.
- 컴포넌트 전반에서 쓰는 인프라 클라이언트(Redis, etcd, 메시지 큐).

## 여기 속하지 않는 것

- 컴포넌트 전용 로직(manager 세션 관리, agent 커널 처리 등).
- `manager/`, `agent/`, `storage/`에서의 import — 의존은 안쪽으로만 흐른다.

## 이 패키지에 추가할 때

- 새 모듈 추가 전, 정말로 여러 컴포넌트가 필요로 하는지 확인한다.
- 단일 컴포넌트 유틸리티는 여기가 아니라 그 컴포넌트 패키지에 둔다.

## 하위 패키지 안내

| 하위 패키지 | 용도 |
|-------------|------|
| `common/events/` | 이벤트 타입 정의·디스패처 — 기존 `AbstractEvent` 서브클래스 참고 |
| `common/bgtask/` | 백그라운드 태스크 프레임워크 — `BaseBackgroundTaskHandler` 확장 |
| `common/dto/` | 컴포넌트 간 DTO — `common/dto/AGENTS.md` 참고 |
| `common/exception.py` | 루트 `BackendAIError`와 `ErrorCode` — 모든 컴포넌트 예외가 여기서 상속 |
| `common/types.py` | 레이어 전반에서 쓰는 공용 기본 타입 |

## 예외

- `common/exception.py`가 루트 계층을 정의한다 — 컴포넌트 전용 예외를 여기 추가하지 않는다.
- 공용 예외 베이스 클래스 추가는 허용, 구체 도메인 예외는 불가.
