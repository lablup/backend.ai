# 용어집: 구조 계층, 구성 요소

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 사용하지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 가속기 플러그인 | accelerator plugin | 가속기를 Backend.AI 와 연결하는 plugin 패키지입니다. |   |   |
| account manager | account manager | 통합 사용자 프로필과 SSO 를 맡는 별도 daemon 입니다. | AccountManager, accountmgr |   |
| Action | action | service operation 을 감싸 권한 검사와 감사, 지표를 구조적으로 적용하는 단위입니다. |   |   |
| adapter | adapter | v2 handler 가 processor 를 직접 호출하는 대신 사용하는, GQL 계층과 공유하는 호출 계층입니다. |   |   |
| Agent Watcher | agent watcher | Agent service 를 감시하고 관리하는 add-on 서비스입니다. |   |   |
| 스코프별 앱 설정 | app config fragment | 한 스코프가 app config key 에 더하는 값을 JSON 문서로 담은 행입니다. | AppConfigFragment, 앱 설정 프래그먼트, 앱 설정 조각 |   |
| App Proxy | app proxy | 세션 의 service port 로 오는 트래픽을 동적으로 라우팅하고 로드밸런싱하는 컴포넌트입니다. | AppProxy, wsproxy, WSProxy, WebSocket Proxy | wsproxy 는 옛 이름입니다. 코드 식별자는 별도로 정리합니다 |
| app proxy coordinator | app proxy coordinator | routing circuit 을 만들고 서비스를 배치하는 app proxy 구성 요소입니다. |   |   |
| app proxy worker | app proxy worker | 트래픽을 전달하는 app proxy 구성 요소입니다. |   |   |
| 브로드캐스트 이벤트 | broadcast event | 모든 subscriber 가 같은 event 를 받는 이벤트입니다. |   |   |
| 클라이언트 SDK | client SDK | Backend.AI 용 Python 클라이언트 SDK 입니다. |   |   |
| common | common | manager, agent, storage, client SDK 가 모두 의존하는 공용 패키지입니다. |   |   |
| console server | console server | cookie 기반 인증을 제공하는 Backend.AI console server 입니다. |   |   |
| controller | controller | session 과 deployment 등의 상태를 바꿀 수 있는 유일한 진입점입니다. |   |   |
| DataLoader | DataLoader | N+1 질의를 막기 위해 여러 노드 참조를 묶어 가져오는 로더입니다. | data loader |   |
| 배포 이력 | deployment history | deployment handler 의 한 번 실행마다 상태 변화와 결과를 남기는 기록입니다. |   |   |
| 배포 정책 | deployment policy | deployment 가 새 revision 을 배포하는 방식을 담는 정책입니다. |   |   |
| 배포 프리셋 자원 슬롯 | deployment preset resource slot | deployment preset 이 선언하는 slot 별 자원량입니다. | 배포 프리셋 리소스 슬롯 |   |
| 배포 리비전 | deployment revision | deployment 설정의 한 시점 snapshot 으로 그 deployment 안에서 번호가 매겨집니다. |   |   |
| 엔티티 | entity | 코드가 엔티티 단위로 나뉘고 scope 안에 담기며 action 이 가리키는 데이터 단위입니다. |   |   |
| 레이블 | entity label | 어느 엔티티에나 붙는 key=value 라벨입니다. | 라벨 |   |
| 이벤트 버스 | event bus | Valkey 로 실시간 정보를 추적하고 시스템 이벤트를 다른 컴포넌트에 알리는 내부 서비스입니다. |   |   |
| kernel runner | kernel runner | kernel 컨테이너 안에서 실행되며 사용자 코드 실행과 컨테이너 안 서비스 프로세스를 관리하는 작은 daemon 입니다. | kernel runtime |   |
| 커널 스케줄링 이력 | kernel scheduling history | 커널이 image pull 부터 종료까지 거친 단계와 그 결과를 기록하는 이력입니다. |   |   |
| Manager | manager | 사용자 요청을 받아 세션을 만들고 agent 에 코드 실행을 라우팅하는 중앙 API gateway 이자 orchestrator 인 컴포넌트입니다. |   |   |
| 모델 카드 자원 요구 사항 | model card resource requirement | model card 가 slot 별로 요구하는 최소 자원량입니다. |   |   |
| processor | processor | handler 가 processor 를 호출하는, action 을 받아 권한 검사와 감사, 지표를 구조적으로 실행하는 계층입니다. |   |   |
| 프로메테우스 쿼리 프리셋 카테고리 | prometheus query preset category | Prometheus query preset 을 묶는 분류입니다. |   |   |
| relation | relation | 두 entity 를 잇거나 끊는, 자기 테이블과 자기 연산을 갖는 세 번째 대상입니다. | 엔티티 관계, 관계 |   |
| 복제본 그룹 이력 | replica group history | replica group handler 의 한 번 실행마다 상태 변화와 결과를 남기는 기록입니다. |   |   |
| repository | repository | 데이터 접근을 담당하는 계층입니다. |   |   |
| resolver | resolver | fetcher 를 호출하는 얇은 GraphQL operation wrapper 계층입니다. |   |   |
| 라우트 이력 | route history | route handler 가 replica 하나에 대해 한 번 실행될 때의 상태 변화와 결과를 남기는 기록입니다. |   |   |
| scheduler | scheduler | 대기 세션을 조회해 agent 에 배치하는 실제 스케줄링 알고리즘을 실행하는 sokovan 엔진입니다. |   |   |
| service | service | 도메인 검증과 business logic 을 두는 계층입니다. | 서비스 |   |
| 세션 에이전트 지정 | session agent designation | 세션을 배치할 agent 를 지정하는 기능입니다. | session designated agent, 세션 지정 에이전트 |   |
| session lifecycle handler | session lifecycle handler | 대상 상태의 세션을 조회해 처리하고 결과에 따라 상태를 전이하는 세션 수명 주기 처리기입니다. | lifecycle handler, 세션 처리기 |   |
| sokovan | sokovan | manager 안에서 coordinator 와 scheduling 을 두는 층입니다. |   |   |
| sokovan coordinator | sokovan coordinator | retry, timeout, give_up 같은 history 기반 판단과 상태 전이를 중앙에서 맡는 sokovan 구성 요소입니다. | coordinator |   |
| 상태 전이 | status transition | 성공, 재시도, 만료, 포기 같은 결과에 따라 상태가 옮겨 가는 흐름입니다. |   |   |
| Storage Proxy | storage proxy | manager 에서 큰 파일 전송을 분담하고 스토리지 벤더 API 를 추상화하는 proxy 컴포넌트입니다. |   |   |
| 사용자 fair share | user fair share | resource group 안에서 user 의 과거 사용량과 weight 로 정해지는 스케줄링 우선순위입니다. |   |   |
| 가상 엔티티 | virtual entity | 실제 entity row 의 권한 그래프 쪽 대응 행으로, virtual_entities 테이블에 있으며 entity 참조의 기준이자 membership edge 의 부모입니다. |   |   |
| webserver | webserver | web UI 를 제공하고 REST와 GraphQL 요청을 Manager 나 Hive Gateway 로 프록시하는 gateway 컴포넌트입니다. |   | 앞으로 gateway 로 바꾸려는 이름입니다. 빌드, 서비스 이름이 바뀔 때까지 유지합니다 |
