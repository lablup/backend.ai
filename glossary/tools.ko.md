# 용어집: 기술, 도구 이름

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 사용하지 않는 어휘 | 메모 |
|---|---|---|---|---|
| Alembic | Alembic | Backend.AI 컴포넌트의 DB schema migration 을 적용하고 롤백하는 도구입니다. |   |   |
| Callosum | Callosum | manager 와 agent 사이 RPC 에 사용하는 ZeroMQ 기반 라이브러리입니다. |   |   |
| cherry-pick | cherry-pick | main 에 먼저 구현한 변경을 x.y release branch 로 옮기는 방법입니다. |   |   |
| deep merge | deep merge | caller 에게 보이는 모든 fragment 를 allow-list rank 오름차순으로 합치되 중첩 객체는 재귀하고 스칼라와 목록은 통째로 교체하는 병합입니다. |   |   |
| distributed lock | distributed lock | manager 가 교체해서 사용하는 분산 잠금 backend 로 filelock, pg_advisory, redlock, etcd, etcetra 중에서 고르고 기본값은 pg_advisory 입니다. | replacible distributed lock backend |   |
| Docker backend | Docker backend | agent 가 여러 container runtime 중 docker 로 kernel container 를 다루는 backend 구현입니다. |   |   |
| Docker Swarm | Docker Swarm | 다중 노드 멀티 커널 세션 의 overlay network 를 구성하는 데 사용하는 기반입니다. | Swarm |   |
| dotfile | dotfile | entity 에 설정하는 사용자 설정 파일 모음입니다. |   |   |
| etcd | etcd | cluster 전역 설정과 manager 상태를 담고 변경 시 hot reload 되는 설정 소스입니다. |   |   |
| FastTrack | FastTrack | manager 위에서 연산 작업 파이프라인을 설계·실행하는 add-on 서비스입니다. |   |   |
| Forklift | Forklift | Backend.AI 호환 컨테이너 이미지를 만들고 가져오는 standalone 서비스입니다. |   |   |
| Graphene | Graphene | manager 의 이전 GraphQL API 를 제공하는 subgraph 로 Strawberry 로 옮겨지는 중입니다. | Legacy GraphQL API |   |
| GraphQL Inspector | GraphQL Inspector | GraphQL schema 의 breaking change 를 검사하는 CI status check 입니다. |   |   |
| Hive Gateway | Hive Gateway | manager 의 GQL subgraph 세 개(graphene, strawberry, public)를 federation 하는 GraphQL gateway 입니다. | Hive Router |   |
| jail | jail | 정책에 따라 일부 system call 을 막는 kernel 실행 환경입니다. | Backend.AI Jail |   |
| Kubernetes backend | Kubernetes backend | agent 의 infrastructure 구현 중 kubernetes 를 다루는 backend 입니다. | k8s |   |
| mock accelerator | mock accelerator | 실제 장치 없이 accelerator 장치가 있는 것처럼 보이게 하는 시뮬레이터 plugin 입니다. | mock, mock-up plugin, mocked Accelerators |   |
| Pants | Pants | build 자동화와 의존성 관리를 맡는 빌드 도구입니다. | Pantsbuild |   |
| presigned URL | presigned URL | object storage 에 직접 올리거나 받을 수 있게 만료 시간이 있는 URL 입니다. |   |   |
| Prometheus | Prometheus | manager 등 컴포넌트의 운영 지표를 수집하는 모니터링 도구입니다. |   |   |
| pydantic | pydantic | 24.03 부터 REST API 요청과 응답 validator 로 사용하는 라이브러리입니다. |   |   |
| SDK | SDK | Backend.AI REST API 를 사용하는 python 라이브러리입니다. |   |   |
| strawberry | strawberry | Manager 의 v2 GraphQL API 를 제공하는 subgraph 입니다. | New GraphQL API, v2 schema |   |
| towncrier | towncrier | changes/ 의 changelog fragment 를 모아 changelog 를 만드는 도구입니다. |   |   |
| Traefik | Traefik | worker 대신 traffic forwarding 을 맡고 coordinator 가 route 를 발행해 읽게 하는 proxy 입니다. | proxy dataplane |   |
| TUS | TUS | resumable upload 방식으로 proxy 가 Valkey lease 로 offset 을 관리합니다. | upload session |   |
| Valkey | Valkey | cache data 를 보유하고 event queue 를 겸하는 의존성입니다. | Redis, 레디스 | 문서 표기 기준입니다. 설정 키와 코드 이름 변경은 별도 작업입니다 |
| VFS storage | VFS storage | storage namespace 뒤의 filesystem backend 입니다. |   |   |
