# 클라이언트 SDK v2: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

REST v2 API 를 위한 typed Python 클라이언트다. 엔티티마다 domain client 하나를 두고, 요청과 응답 모델은 서버와 같은 Pydantic 모델(`common/dto/manager/v2/`)을 사용한다. 프로그램으로 API 를 사용하는 쪽이 직접 HTTP 를 작성하지 않고, 검증되는 하나의 경로로 API 를 호출하게 하려고 둔다.

- **CLI**(`client/cli/v2/`)가 이 패키지를 기반으로 한다.
- **통합 테스트**가 이 패키지로 실행 중인 서버를 호출한다.
- SDK 메서드가 없는 v2 엔드포인트는 CLI 와 통합 테스트 양쪽에서 보이지 않는다. 엔드포인트를 배포하는 일에는 client 메서드를 배포하는 일이 포함된다.

## scoped search 통합: 서버는 마쳤고 SDK 는 남았다

- 지금 SDK 는 스코프마다 메서드를 따로 둔다. `project_search(project_id, request)`, `domain_search(domain_name, request)` 가 부모가 고정된 URL 로 대응한다.
- 서버는 BA-7742 에서 자기 쪽을 마쳤다. `POST /{entity}/scoped/search` 는 종류별 `UUIDScope` 목록을 담은 `scope` 객체를 받고 모두 OR 로 묶는다. 스코프별 route 는 그 옆에 남는다. URL 패턴과 요청 모양은 더 이상 미정이 아니다.
- 남은 것은 SDK 의 엔티티별 `scoped_search(request)` 하나와 그것을 호출하는 CLI 옵션이다. 그 작업이 들어오기 전까지 새 SDK 코드는 지금의 스코프별 모양을 따르고, 한 엔티티 안에서 두 모양을 섞지 않는다.
- 지금 모양은 스코프 종류가 늘 때마다 엔티티마다 메서드가 하나씩 늘어난다. 서버가 엔티티를 전환할 때마다 서버의 scoped 엔드포인트와의 차이가 커진다.
