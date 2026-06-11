# Agent — 가드레일

> 컴포넌트 전체 개요는 `src/ai/backend/agent/README.md`.

## 예외

- 새 예외는 `agent/errors/`에 정의한다 — `agent/exception.py`는 legacy.

## 컨테이너 라이프사이클

- 컨테이너 상태 전이는 `agent/stage/`의 상태 머신을 거쳐야 한다.
- 라이프사이클 핸들러 밖에서 컨테이너 상태를 바꾸는 직접 Docker/K8s API 호출 금지.
- 헬스체크·하트비트 로직은 `agent/health/`에 둔다 — 메인 루프에 인라인 금지.

## 인프라 구현 (Docker / Kubernetes / Dummy)

- 구현 전 항상 `agent/`의 추상 베이스 클래스를 확인한다.
- Dummy 구현은 Docker/Kubernetes 변경과 함께 갱신해야 한다.
- 인프라별 신규 코드는 해당 하위 디렉터리(`agent/docker/`, `agent/kubernetes/`, `agent/dummy/`)에 둔다.

## Manager 통신

- Agent → Manager 통신은 이벤트 시스템만 쓴다.
- Manager 직접 RPC 호출은 지정된 RPC Server 진입점에서만 허용.
- Agent 비즈니스 로직 안에서 Manager로의 새 직접 HTTP 호출을 추가하지 않는다.

## 리소스 추적

- 리소스 할당/해제는 `alloc_map.py`를 거쳐야 한다.
- `alloc_map.py` 밖에서 리소스 카운터를 직접 조작하지 않는다.
