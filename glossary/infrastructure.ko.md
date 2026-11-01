# 용어집: 인프라

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 쓰지 않는 어휘 | 메모 |
|---|---|---|---|---|
| AppProxy tunnel | AppProxy tunnel | 컨테이너에 접근할 때 쓰는 AppProxy 경로입니다. | App Proxy tunnel |   |
| bai | bai | Backend.AI v2 CLI 명령입니다. | v2 CLI |   |
| BEP | BEP | Backend.AI Enhancement Proposal, 설계 배경을 담은 제안 문서입니다. |   |   |
| Event Stream API | Event Stream API | Server-Sent Events 로 event 를 내보내는 manager API 입니다. | Server-Sent Events |   |
| halfstack | halfstack | Docker Compose 로 띄우는 개발 환경 구성으로 PostgreSQL, etcd, Valkey 컨테이너를 담습니다. | Backend.AI halfstack |   |
| 설치 채널 | installer channel | 레지스트리에서 최신 maintained version 과 최신 LTS 를 읽어 정하는 설치 채널입니다. |   |   |
| 로컬 설정 | local config | 각 컴포넌트의 TOML 설정으로 boot 때 읽어 재시작해야 반영됩니다. | local config 파일 |   |
| LTS | LTS | 1년 지원을 약속하는 release line 입니다. | long-term support |   |
| 관리 노드 | management node | agent 를 제외한 대부분 컴포넌트를 설치하는 노드입니다. |   |   |
| 마운트 경로 | mount path | vfolder 가 container 에 마운트되는 경로입니다. |   |   |
| 오버레이 네트워크 | overlay network | 여러 agent 에 걸친 멀티 커널 세션 에서 manager 가 자동 구성하는 네트워크입니다. | private overlay network |   |
| 사설 브리지 네트워크 | private bridge network | 단일 노드 멀티 커널 세션 의 container 들이 사적으로 통신하는 네트워크입니다. |   |   |
| 프로필 | profile | endpoint 와 계정, session 을 하나로 묶어 저장하는 CLI 접속 정보 단위입니다. |   |   |
| RC | RC | release 후보를 가리키는 release type 값입니다. | Release Candidate |   |
| resource-seconds | resource-seconds | 자원량에 사용 기간의 초를 곱한 사용량 단위로 capacity 의 raw unit 과 섞지 않습니다. |   |   |
| stable | stable | installer 다운로드 링크 중 최신 LTS version 을 가리키는 채널입니다. |   |   |
| 스토리지 백엔드 | storage backend | storage volume 이 놓이는 storage appliance 를 가리키는 정규화된 레코드입니다. |   |   |
| 스토리지 백엔드 유형 | storage backend type | volume 을 서비스할 수 있는 storage backend 구현입니다. |   |   |
| v1 CLI | v1 CLI | v2 CLI 와 분리된 legacy CLI 로 쓰지 말라고 안내합니다. |   |   |
| WebUI | WebUI | manager 의 GraphQL API 를 주로 소비하는 웹 클라이언트입니다. |   |   |
