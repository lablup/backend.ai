# Manager DTO: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

예전에는 manager 전용 API handler 의 통신 타입을 담았다. 지금은 사실상 legacy 표면의 묶음이다. 아래에서 설명한다.

## 실제 경계는 대상이 아니라 API 버전이다

- 명목상 경계는 대상 범위(manager 전용/공유)지만, 새 기능의 DTO 는 모두 `common/dto/manager/v2/` 로 간다(GraphQL 과 REST v2 가 공유한다).
- 그래서 이 패키지는 사실상 **REST v1 / legacy handler 묶음**이고, 소비자는 거의 전부 v1 handler 다.
- 아직 이전할 수 없는 v1 표면을 확장할 때만 여기에 추가한다.

## base class 는 하나가 아니라 셋이다

- 요청: `BaseRequestModel` / 응답: `BaseResponseModel` / middleware 가 주입하는 context(`RequestCtx`, `UserContext` 등): `from_request()` 생성자를 가진 `MiddlewareParam`.
- 셋 모두 `ai.backend.common.api_handlers` 에서 온다.

## 알려진 계층 이탈: 확장하지 않는다

- 일부는 자기 계층 아래까지 접근한다. `request.py` 는 `to_updater()` 를 제공하려고 ORM row 와 repository updater 를 가져오고, `context.py` 는 models 의 enum 을 가져온다.
- 계층 규칙보다 먼저 생긴 코드다. 새 코드는 이를 따르지 않는다. 변환은 adapter 의 일이고 DTO 는 순수하게 유지한다.
