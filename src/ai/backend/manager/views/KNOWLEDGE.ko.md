# Manager views: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있다.

## 이 패키지가 있는 이유

내부 의사 결정(scheduler, coordinator, reconciler)이 받는 입력의 모양을 담는 read projection 공간이다. API 에 묶인 값(`data/`)과 분리해 두면 의사 결정 모양이 API 계약에 끌려다니지 않는다.

## view 는 entity 를 비추지 않는 결정 조각이다

- view 는 결정 하나가 받는 입력의 모양이다. entity 하나가 여러 view 를 갖는 것이 정상이다(replica group 은 reconcile 단계마다 하나씩 다섯 개를 가지며 `{Entity}{Stage}View` 라는 이름을 사용한다).
- **어느 테이블에도 없는 파생 집계**(live/serving/target 수)는 일급 field 이다. repository 가 집계를 수행하고 view 는 그 결과의 모양이다.
- view 는 자식 view 를 중첩할 수 있다(종료 중인 session 은 종료 중인 kernel 을 가진다). `data/` 타입은 일반적으로 그렇지 않다.

## 의존은 한 방향이고 내부 동작을 다루는 곳에는 view 를 권장한다

- `views/` 는 `data/` 와 `common` 의 식별자/schema 를 가져올 수 있지만 그 반대는 안 된다.
- 지금 가장 큰 소비자는 sokovan 이고(`views/sokovan/` 아래 거의 모든 모듈), sokovan 전용은 아니다. **내부 동작만 다루는 객체에는 view 사용을 권장한다**.
- 예정된 소비자: entity lifecycle 관리자(user, project, vfolder, image 등의 lifecycle 을 다루는 객체)도 주로 view 를 사용한다.
- 추가 기준: "내부 결정에 필요한 조각인가". 같은 모양이 API payload 에 나올 수 있으면 `data/` 에 둔다.
