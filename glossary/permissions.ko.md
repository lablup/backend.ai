# 용어집: 권한

문체 규칙은 [용어집](../GLOSSARY.ko.md)을 따릅니다.

| 한글 | English | 뜻 | 사용하지 않는 어휘 | 메모 |
|---|---|---|---|---|
| 이중 인증 | 2FA | 설정하면 login 시 이중 인증 코드를 요구하는 인증 기능입니다. | two-factor authentication, 이중인중 활성화 |   |
| 액세스 키 | access key | keypair 인증에서 프로그래밍 접근에 사용하는 키입니다. | 접근 키 |   |
| admin_ | admin_ | superadmin 전용 동작에 붙는 API 접두사입니다. |   | 코드 이름입니다 |
| 에이전트 선택 정책 | agent selection policy | designated_agent_ids 를 강제할지 대체를 허용할지 정하는 방식입니다. |   |   |
| 허용된 클라이언트 IP | allowed client ip | 지정하면 그 주소에서만 login 할 수 있게 하는 client IP 목록입니다. |   |   |
| 허용된 컨테이너 레지스트리 | allowed container registry | domain 에서 허용하는 container registry 목록입니다. | allowed docker registries, 허용 Docker 레지스트리 |   |
| 허용된 자원 그룹 | allowed resource group | domain 이나 project 가 쓸 수 있도록 허용된 resource group 목록입니다. | 허용 자원 그룹 |   |
| 허용된 스토리지 호스트 | allowed storage host | domain 이 허용하는 storage host 목록입니다. | allowed vfolder hosts, 가상 폴더 호스트 | 앞으로 storage group 으로 통합합니다 |
| API 키페어 | API keypair | 프로그래밍 접근에 사용하는 access key 와 secret key 짝입니다. |   |   |
| 인증 방식 | authentication mode | 사용자 계정의 인증 방식으로 브라우저 세션 기반 session 과 access/secret key 짝의 keypair 가 있습니다. |   |   |
| authority | authority | appproxy worker 노드들이 등록하는 식별 문자열입니다. |   | 앞으로 ingress group 으로 옮깁니다 |
| 클라이언트 IP 허용 목록 | client IP allowlist | 회선이 허용한 주소에서만 공개된 앱에 접근하게 하는 기능입니다. |   |   |
| 클라이언트 IP 마스킹 정책 | client IP masking policy | client 주소를 login history 나 audit log 에 저장하기 전에 어떻게 가릴지 정하는 정책입니다. |   |   |
| 기본 액세스 키 | default access key | 사용자가 대표로 사용하는 access key 이며 다른 key 로 바꿀 수 있습니다. | 기본 키페어, main access key | 코드 에러 문구는 이미 default access key 입니다 |
| 배포 토큰 | deployment token | deployment 를 호출하는 token 으로, 어떤 사용자로 행동할지 고정합니다. | access token, 액세스 토큰, 접근 토큰, deployment access token |   |
| 도메인 관리자 | domain admin | domain scope 안에서 전체 권한을 가지는 관리자 역할입니다. |   | RBAC 역할로만 있습니다 |
| 도메인 멤버 | domain member | domain scope 의 기본 구성원 역할입니다. |   |   |
| 최종 적용 권한 | effective permission | 여러 역할 부여와 cap 을 합쳐 실제로 적용되는 권한입니다. | 실효 권한 |   |
| 엔티티 공유 | entity share | 한 entity 를 다른 사용자나 project 에 제안해 넘겨 주는 권한 부여입니다. | invitation, offer |   |
| gate | gate | action 실행을 검사하고 각 scope 를 허가하는 validator 입니다. |   |   |
| 유휴 검사기 할당 | idle checker assignment | global idle checker 를 scope 하나에 묶는 배정입니다. | idle checker binding |   |
| 사용자 가장 | impersonation | super admin 이 대상 사용자의 권한 맥락으로 작업을 실행하게 하는 기능입니다. | Act As |   |
| 키페어 | keypair | user 가 API 호출에 서명하는 access key 와 secret key 짝입니다. | 키 쌍, 키 페어 |   |
| 키페어 자원 정책 | keypair resource policy | keypair 에 묶여 세션 관련 자원 한도를 제어하는 자원 정책입니다. |   | 제거 예정입니다. 새로 쓰지 않습니다 |
| 마운트 정책 | mount policy | 한 user 가 한 vfolder 에 갖는 mount 수준으로 none, ro, rw 값을 가집니다. |   |   |
| my | my | 현재 사용자 자신의 자원만 다루는 연산 접두사입니다. |   |   |
| 권한 | permission | role 이 한 scope 안에서 한 entity type 에 부여하는 권한 하나입니다. |   |   |
| 권한 비트 | permission bit | permission mask 의 한 bit 로 부여된 동작을 나타내는 값입니다. |   |   |
| 프로젝트 관리자 | project admin | project scope 안에서 전체 권한을 가지는 관리자 역할입니다. |   | RBAC 역할로만 있습니다 |
| 프로젝트 멤버 | project member | project scope 의 기본 구성원 역할입니다. |   |   |
| 프로젝트 자원 정책 | project resource policy | project 단위 자원의 공유 쿼터를 제어하는 자원 정책입니다. |   |   |
| public | public | 권한 검사 없이 인증된 모든 사용자에게 허용하는 연산 접두사입니다. 익명 접근은 아닙니다. |   |   |
| RBAC | RBAC | role 과 scope 종류, entity 종류, permission bit 조합으로 권한을 표현하는 체계입니다. | Role-Based Access Control |   |
| 자원 정책 | resource policy | keypair, user, project 별로 자원 한도를 정하는 정책입니다. | 리소스 정책 |   |
| 역할 | role | 권한을 묶어 scope 안에서 사용자에게 부여하는 단위입니다. |   |   |
| 역할 할당 | role assignment | 사용자와 role 을 잇는 할당 관계입니다. 회수하면 row 가 삭제됩니다. |   |   |
| 권한 프리셋 | role permission preset | role preset 이 부여하는 권한 항목입니다. | permission entry, 권한 항목, 프리셋 권한 |   |
| 역할 프리셋 | role preset | role 을 만들 때 사용하는 template 이며 seed YAML 로 적재됩니다. |   |   |
| 역할 상태 | role status | role 상태 값 묶음으로 inactive 는 일시 비활성, deleted 는 영구 제거를 뜻합니다. |   |   |
| RPC 키페어 | RPC keypair | manager 와 agent 사이 RPC 인증과 암호화에 사용하는 keypair 입니다. |   |   |
| 스코프 | scope | 접근 경계를 정의하는 범위로 domain, project, user 같은 단위입니다. |   |   |
| 스코프 상한 | scope cap | scope 단위로 granted 권한을 좁히는 상한입니다. |   |   |
| 스코프 권한 | scoped permission | 특정 스코프 안의 entity 타입에 대한 연산 권한입니다. | Scope-Level Permission |   |
| secret key | secret key | API keypair 에서 access key 와 짝을 이루는 비밀 키입니다. | 시크릿 키, 비밀 키 | pk, sk 의 비밀 키와 다른 개념입니다 |
| SSH 키페어 | SSH keypair | user 가 소유하는 SSH keypair 로 SSH/SFTP 접근에 쓰입니다. |   |   |
| storage proxy client API | storage proxy client API | Storage Proxy 에서 사용자에게 열린 API 입니다. | client-facing API, client API |   |
| storage proxy manager API | storage proxy manager API | Storage Proxy 에서 Manager 가 호출하는 API 입니다. | manager-facing API |   |
| sudo 세션 | sudo session | user 가 만들 수 있는 privileged session 입니다. |   |   |
| superadmin | superadmin | role row 없이 모든 권한 검사를 통과하는 시스템 전체 관리자입니다. | suerp-admin, super-admin, 슈퍼관리자, 슈퍼 관리자 |   |
| vfolder 권한 | vfolder permission | 한 사용자가 한 vfolder 에 갖는 권한입니다. | 폴더 권한 | 앞으로 mount 정책 외에는 RBAC 으로 통합합니다 |
| 가상 스코프 | virtual scope | 소유 스코프마다 하나씩 두는 권한 판정 허브 노드입니다. |   |   |
